import logging

#logging.basicConfig(level=logging.ERROR)


class CardInfoHelper(object):
    def __init__(self, app):
        self.app = app

    def get_title(self, key):
        raise NotImplemented


class JIRAHelper(CardInfoHelper):
    def __init__(self, app, username, password):
        self.app = app
        self.wsdl_url = app.config['JIRA_WSDL']
        from suds.client import Client
        self.Client = Client

        self.service = self.connect(username, password)

    def connect(self, username, password):
        client = self.Client(self.wsdl_url)
        auth = client.service.login(username, password)
        self.auth = auth
        return client.service

    def get_title(self, key):
        issue = self.service.getIssue(self.auth, key)
        return issue.summary