from mock import Mock

class MockJIRAIssue(Mock):
    summary = "There's been a lot of lies in this family"

class MockJIRAService(Mock):
    def getIssue(self, auth, key):
        return MockJIRAIssue()

class MockJIRAClient(Mock):
    service = MockJIRAService()
