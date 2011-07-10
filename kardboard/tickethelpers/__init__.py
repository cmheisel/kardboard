import logging
from kardboard.util import ImproperlyConfigured


class TicketHelper(object):
    def __init__(self, app, kard):
        self.app = app
        self.kard = kard

    def get_title(self, key=None):
        raise NotImplemented

    def get_ticket_url(self, key=None):
        raise NotImplemented


class TestTicketHelper(TicketHelper):
    def get_title(self, key=None):
        return u"""Dummy Title from Dummy Ticket System"""

    def get_ticket_url(self):
        return u"""http://example.com/ticket/%s""" % self.kard.key


class JIRAHelper(TicketHelper):
    def __init__(self, app, kard):
        super(JIRAHelper, self).__init__(app, kard)

        try:
            self.wsdl_url = app.config['JIRA_WSDL']
        except KeyError:
            raise ImproperlyConfigured("You must provide a JIRA_WSDL setting")

        try:
            self.username, self.password = app.config['JIRA_CREDENTIALS']
        except KeyError:
            raise ImproperlyConfigured(
                "You must provide a JIRA_CREDENTIALS setting")
        except ValueError:
            raise ImproperlyConfigured(
                "JIRA_CREDENTIALS should be a two-item tuple (user, pass)")

        from suds.client import Client
        self.Client = Client
        self.connect()

    def connect(self):
        client = self.Client(self.wsdl_url)
        auth = client.service.login(self.username, self.password)
        self.auth = auth
        self.service = client.service

    def get_title(self, key=None):
        if not key:
            key = self.kard.key
        issue = self.service.getIssue(self.auth, key)
        return issue.summary

    def get_ticket_url(self, key=None):
        raise NotImplemented
