from mock import Mock


class MockJIRAIssue(Mock):
    summary = "There's been a lot of lies in this family"
    status = '6'

class MockJIRAService(Mock):
    def getIssue(self, auth, key):
        return MockJIRAIssue()

    def getStatuses(self):
        return [{
            'description': '',
            'icon': 'http://jira.example.com/images/icons/status_closed.gif',
            'id': '6',
            'name': 'Closed',
        }, ]


class MockJIRAClient(Mock):
    service = MockJIRAService()
