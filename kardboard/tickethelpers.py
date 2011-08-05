import urlparse
import datetime

from kardboard.models import Kard
from kardboard import cache
from kardboard.util import ImproperlyConfigured, log_exception
from kardboard.tasks import update_ticket


class TicketHelper(object):
    def __init__(self, config, kard):
        self.app_config = config
        self.card = kard

    def get_title(self, key=None):
        raise NotImplemented

    def get_ticket_url(self, key=None):
        raise NotImplemented

    def update(self, sync=False):
        now = datetime.datetime.now()
        self.card._ticket_system_updated_at = now

    def actually_update(self):
        raise NotImplemented


class NullHelper(TicketHelper):
    def get_title(self, key=None):
        return ''

    def get_ticket_url(self, key=None):
        return ''

    def update(self, sync=False):
        super(NullHelper, self).update(sync)
        return None

    def actually_update(self):
        return None


class TestTicketHelper(TicketHelper):
    def get_title(self, key=None):
        title = ''
        if self.card._ticket_system_data:
            title = self.card._ticket_system_data.get('summary', '')
        else:
            self.card.ticket_system.update(sync=True)
            title = self.card.ticket_system_data.get('summary', '')
        return title

    def get_ticket_url(self):
        return u"""http://example.com/ticket/%s""" % self.card.key

    def update(self, sync=False):
        super(TestTicketHelper, self).update()
        test_data = {
            'summary': u"""Dummy Title from Dummy Ticket System""",
        }
        self.card._ticket_system_data = test_data

class JIRAHelper(TicketHelper):
    def __init__(self, config, kard):
        super(JIRAHelper, self).__init__(config, kard)
        from kardboard import app
        self.logger = app.logger
        self.testing = app.config.get('TESTING')
        self.issues = {}
        self._service = None

        try:
            self.wsdl_url = self.app_config['JIRA_WSDL']
        except KeyError:
            raise ImproperlyConfigured("You must provide a JIRA_WSDL setting")

        try:
            self.username, self.password = self.app_config['JIRA_CREDENTIALS']
        except KeyError:
            raise ImproperlyConfigured(
                "You must provide a JIRA_CREDENTIALS setting")
        except ValueError:
            raise ImproperlyConfigured(
                "JIRA_CREDENTIALS should be a two-item tuple (user, pass)")

    @property
    def cache_prefix(self):
        return "jira_%s" % self.wsdl_url

    @property
    def service(self):
        if self._service is None:
            from suds.client import Client
            self.Client = Client
            self.connect()
        return self._service


    def connect(self):
        auth_key = "offline_auth_%s" % self.cache_prefix
        auth = cache.get(auth_key)

        client = self.Client(self.wsdl_url)
        if not auth:
            self.logger.warn("Cache miss for %s" % auth_key)
            auth = client.service.login(self.username, self.password)
            cache.set(auth_key, auth, 60 * 60)  # Cache for an hour

        self.auth = auth
        self._service = client.service

    def get_issue(self, key=None):
        key = key or self.card.key
        if self.issues.get(key, None):
            return self.issues.get(key)

        issue = self.service.getIssue(self.auth, key)
        self.issues[key] = issue
        return issue

    def get_title(self, key=None):
        title = ''
        if self.card._ticket_system_data:
            title = self.card._ticket_system_data.get('summary', '')
        else:
            self.card.ticket_system.update(sync=True)
            title = self.card.ticket_system_data.get('summary', '')
        return title

    def issue_to_dictionary(self, obj):
        idic = {}
        keys = ['summary', 'key', 'reporter', 'assignee', 'description',
            'status', 'type']
        for key in keys:
            idic[key] = getattr(obj, key)
        idic['status'] = self.resolve_status(idic['status'])
        idic['type'] = self.resolve_type(idic['type'])
        return idic

    def object_to_dict(self, obj):
        keys = [k for k in dir(obj) if not k.startswith("_")]
        dic = dict([(key, getattr(obj, key)) for key in keys])
        return dic

    def resolve_status(self, status_id):
        key = "%s_statuses" % self.cache_prefix
        statuses = cache.get(key)
        if not statuses:
            self.logger.warn("Cache miss for %s" % key)
            statuses = self.service.getStatuses()
            statuses = [self.object_to_dict(s) for s in statuses]
            cache.set(key, statuses)
        status = [s for s in statuses if s['id'] == status_id]
        try:
            return status[0]
        except IndexError:
            self.logger.warn("Couldn't find status_id: %s in %s" %
                (status_id, statuses))
            return {}

    def resolve_type(self, type_id):
        key = "%s_issue_types" % self.cache_prefix
        the_types = cache.get(key)
        if not the_types:
            self.logger.warn("Cache miss for %s" % key)
            the_types = self.service.getIssueTypes()
            the_types = [self.object_to_dict(t) for t in the_types]
            cache.set(key, the_types)
        the_type = [t for t in the_types if t['id'] == type_id]
        try:
            return the_type[0]
        except IndexError:
            type_help = ["%s -- %s" % (t['id'], t['name']) \
                for t in the_types]
            self.logger.warn("Couldn't find type_id: %s in %s" %
                (type_id, type_help))
            return {}

    def update(self, sync=False):
        if self.card._ticket_system_data and self.card.id:
            if sync:
                self.actually_update()
            else:
                update_ticket.apply_async((self.card.id,))
        else:
            # first fetch
            self.actually_update()

    def actually_update(self):
        super(JIRAHelper, self).update()
        self.logger.info("Fetching JIRA data for %s" % self.card.key)
        try:
            issue = self.get_issue(self.card.key)
        except Exception:
            issue = None
            log_exception("Couldn't fetch JIRA issue %s" % self.card.key)
        if issue:
            issue_dict = self.issue_to_dictionary(issue)
        elif self.card._ticket_system_data:
            return None
        else:
            # We want to ensure there's at least an empty dict
            issue_dict = {}
            return None

        now = datetime.datetime.now()
        self.card._ticket_system_data = issue_dict
        self.card._ticket_system_updated_at = now
        if self.card.id:
            Kard.objects(id=self.card.id).update_one(
                set___ticket_system_data=issue_dict)
            Kard.objects(id=self.card.id).update_one(
                set___ticket_system_updated_at=now)
            self.card.reload()
            self.logger.info(
                "%s updated at %s" % (self.card.key,
                    self.card._ticket_system_updated_at))

    def get_ticket_url(self, key=None):
        key = key or self.card.key
        parsed_url = urlparse.urlparse(self.wsdl_url)
        browse_url_parts = [
            parsed_url.scheme,
            '://',
            parsed_url.netloc,
            '/browse/',
            key,
        ]
        return ''.join(browse_url_parts)
