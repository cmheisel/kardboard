import urlparse
import logging

from kardboard.util import ImproperlyConfigured

class TicketHelper(object):
    def __init__(self, config, kard):
        self.app_config = config
        self.card = kard

    def get_title(self, key=None):
        raise NotImplemented

    def get_ticket_url(self, key=None):
        raise NotImplemented


class TestTicketHelper(TicketHelper):
    def get_title(self, key=None):
        return u"""Dummy Title from Dummy Ticket System"""

    def get_ticket_url(self):
        return u"""http://example.com/ticket/%s""" % self.card.key

class JIRAConnection(object):
    __shared_state = {}

    def __init__(self, client):
        self.__dict__ = self.__shared_state
        self.client = client

    def connect(self, username, password):
        self.auth = self.client.service.login(username, password)
        return self.auth


class JIRAHelper(TicketHelper):
    def __init__(self, config, kard):
        super(JIRAHelper, self).__init__(config, kard)
        self.logger = logging.getLogger('kardboard.tickethelpers.JIRAHelper')
        self.issues = {}

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

        from suds.client import Client
        self.Client = Client

    def connect(self):
        client = self.Client(self.wsdl_url)
        jc = JIRAConnection(client)  # Avoid double-login
        if hasattr(jc, 'auth'):
            auth = jc.auth
        else:
            auth = jc.connect(self.username, self.password)

        self.auth = auth
        self.service = client.service

    def get_issue(self, key=None):
        if not hasattr(self, 'service'):
            self.connect()

        key = key or self.card.key
        if self.issues.get(key, None):
            return self.issues.get(key)

        self.logger.info("Fetching JIRA issue %s via API" % key)
        issue = self.service.getIssue(self.auth, key)
        self.issues[key] = issue
        return issue

    def get_title(self, key=None):
        issue = self.get_issue(key)
        return issue.summary

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
