import urlparse
import datetime
import cPickle as pickle

from kardboard.app import cache
from kardboard.app import app
from kardboard.util import ImproperlyConfigured, log_exception
from kardboard.tasks import update_ticket


class TicketHelper(object):
    def __init__(self, config, kard):
        self.app_config = config
        self.card = kard

    def get_title(self, key=None):
        """
        The title of the ticket
        """
        pass

    def get_ticket_url(self, key=None):
        """
        A URL to the ticket in the orignating system.
        """
        pass

    def update(self, sync=False):
        """
        Schedules a job to update the ticket from its originating system.

        If sync is True, then the call is executed immediately as a blocking IO task.
        """
        now = datetime.datetime.now()
        self.card._ticket_system_updated_at = now

    def actually_update(self):
        """
        Method called by the scheduled task. Updates the ticket from the originating system.
        """
        pass

    def login(self, username, password):
        """
        Method used to authenticate a user. If successfull, it returns True.
        """
        pass

    @property
    def service_class(self):
        return self.get_service_class()

    def get_service_class(self):
        """
        Method called to extract, if any, the service class from the upstream ticket system.
        For example: Bug, Feature, Expedite, etc.
        """
        pass

    def get_version(self):
        """
        Method called to extract, if any, the version from the upstream ticket system.
        """
        pass


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

    def login(self, username, password):
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

    def login(self, username, password):
        return True

    def get_version(self):
        if self.card:
            return self.card._version
        else:
            return None


class JIRAHelper(TicketHelper):
    clients = {}

    def __init__(self, config, kard):
        super(JIRAHelper, self).__init__(config, kard)
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
            self.connect()
        return self._service

    def connect(self):
        auth_key = "offline_auth_%s" % self.cache_prefix
        auth = cache.get(auth_key)

        client = self.clients.get(self.wsdl_url, None)
        if not client:
            from suds.client import Client
            client = Client(self.wsdl_url)

            #We cache the client because there's
            #major overhead in instantiating
            #and the initial connection
            #and since this mostly is run
            #by a long running celeryd
            #process a simple in-memory
            #cache suffices
            self.clients[self.wsdl_url] = client

        if not auth:
            self.logger.warn("Cache miss for %s" % auth_key)
            auth = client.service.login(self.username, self.password)
            cache.set(auth_key, auth, 60 * 60)  # Cache for an hour

        self.auth = auth
        self._service = client.service

    def login(self, username, password):
        if not self._service:
            self.connect()
        auth = self._service.login(username, password)
        return auth

    def get_issue(self, key=None):
        key = key or self.card.key
        if self.issues.get(key, None):
            return self.issues.get(key)

        issue = self.service.getIssue(self.auth, key)
        self.issues[key] = issue
        return issue

    def get_title(self, key=None):
        title = ''
        if not self.card._ticket_system_data:
            self.card.ticket_system.update(sync=True)
        title = self.card.ticket_system_data.get('summary', '')
        return title

    def get_version(self, key=None):
        version = ''
        if not self.card._ticket_system_data:
            self.card.ticket_system.update(sync=True)
        versions = self.card.ticket_system_data.get('fixVersions', [])
        if versions:
            try:
                version = versions[0]['name']
            except IndexError:
                print versions
                raise
        return version

    def get_service_class(self, key=None):
        service_class = None
        if not self.card._ticket_system_data:
            self.card.ticket_system.update(sync=True)
        service_class = self.card._ticket_system_data.get('type', {}).get('name', '')
        return service_class

    def issue_to_dictionary(self, obj):
        idic = {}
        keys = ['summary', 'key', 'reporter', 'assignee', 'description',
            'status', 'type', 'updated', 'fixVersions']
        for key in keys:
            idic[key] = getattr(obj, key)
        idic['status'] = self.resolve_status(idic['status'])
        idic['type'] = self.resolve_type(idic['type'])
        idic['fixVersions'] = [self.object_to_dict(v) for v in idic['fixVersions']]

        return idic

    def object_to_dict(self, obj):
        keys = [k for k in dir(obj) if not k.startswith("_")]
        dic = dict([(key, getattr(obj, key)) for key in keys])
        return dic

    def resolve_status(self, status_id):
        key = "%s_statuses" % self.cache_prefix
        statuses = cache.get(key)
        if statuses:
            try:
                statuses = pickle.loads(statuses)
            except pickle.UnpicklingError:
                statuses = None
        if not statuses:
            self.logger.warn("Cache miss for %s" % key)
            statuses = self.service.getStatuses()
            statuses = [self.object_to_dict(s) for s in statuses]
            cache.set(key, pickle.dumps(statuses))
        status = [s for s in statuses if s.get('id') == status_id]
        try:
            return status[0]
        except IndexError:
            self.logger.warn("Couldn't find status_id: %s in %s" %
                (status_id, statuses))
            return {}

    def resolve_type(self, type_id):
        key = "%s_issue_types_and_subtasks" % self.cache_prefix
        the_types = cache.get(key)
        the_types = None
        if the_types:
            try:
                the_types = pickle.loads(the_types)
            except pickle.UnpicklingError:
                the_types = None
        if the_types == None:
            self.logger.warn("Cache miss for %s" % key)
            the_types = self.service.getIssueTypes()
            the_types = [self.object_to_dict(t) for t in the_types]
            the_subtask_types = self.service.getSubTaskIssueTypes()
            the_subtask_types = [self.object_to_dict(st) for st in the_subtask_types]
            the_types.extend(the_subtask_types)
            cache.set(key, pickle.dumps(the_types))
        the_type = [t for t in the_types if t['id'] == type_id]
        try:
            return the_type[0]
        except IndexError:
            type_help = ["%s -- %s" % (t['id'], t['name']) \
                for t in the_types]
            self.logger.warn("Couldn't find type_id: %s in %s" %
                (type_id, type_help))
            return {}

    def update(self, issue=None, sync=False):
        if self.card._ticket_system_data and self.card.id:
            if sync:
                self.actually_update(issue)
            else:
                update_ticket.apply_async((self.card.id,))
        else:
            # first fetch
            self.actually_update(issue)

    def _get_custom_field_values(self, field_id, fields):
        for field in fields:
            if field.customfieldId == 'customfield_%s' % field_id:
                return field.values
        return None

    def id_devs(self, issue):
        backend_developer_id = 10210
        ui_devs_id = 10211
        custom_fields = issue.customFieldValues
        be_devs = self._get_custom_field_values(backend_developer_id, custom_fields)
        ui_devs = self._get_custom_field_values(ui_devs_id, custom_fields)

        devs = []
        if be_devs:
            devs = devs + be_devs
        if ui_devs:
            devs = devs + ui_devs

        return list(set(devs))

    def id_testers(self, issue):
        qa_resource_id = 10133
        custom_fields = issue.customFieldValues
        qaers = self._get_custom_field_values(qa_resource_id, custom_fields)
        if not qaers:
            return []
        return list(set(qaers))

    def update_state(self, card):
        mappings = app.config.get('TICKET_STATE_MAPPING', {})
        if not mappings:
            return card  # Short circuit

        current_ticket_status = \
            card._ticket_system_data.get(u'status', {}).get(u'name', '')

        state, datefield = mappings.get(current_ticket_status, (None, None))
        if state:
            oldstate = card.state
            if card.state != state:
                card.state = state
                self.logger.info(
                    "AUTOMOVE: %s state moved %s => %s because status was %s" % (self.card.key,
                        oldstate, card.state, current_ticket_status))
        if datefield:
            current_value = getattr(card, datefield)
            if not current_value:
                setattr(card, datefield, datetime.datetime.now())
                self.logger.info(
                    "AUTOMOVE: %s %s set to %s because status was %s" % (self.card.key,
                    datefield, getattr(card, datefield), current_ticket_status))

        return card

    def actually_update(self, issue=None):
        super(JIRAHelper, self).update()

        if not issue:
            self.logger.info("Fetching JIRA data for %s" % self.card.key)
            try:
                issue = self.get_issue(self.card.key)
            except Exception:
                issue = None
                log_exception("Couldn't fetch JIRA issue %s" % self.card.key)

        if issue:
            issue_dict = self.issue_to_dictionary(issue)

            # TODO: This is super specific to CMG's JIRA setup. Fixme.
            issue_dict['developers'] = self.id_devs(issue)
            issue_dict['testers'] = self.id_testers(issue)

        elif self.card._ticket_system_data:
            return None
        else:
            # We want to ensure there's at least an empty dict
            issue_dict = {}
            return None

        now = datetime.datetime.now()
        self.card._ticket_system_data = issue_dict
        self.card._ticket_system_updated_at = now
        self.card = self.update_state(self.card)
        if self.card.id:
            self.card.save()

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
