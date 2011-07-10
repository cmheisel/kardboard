from mock import Mock

class MockJIRAHelper(Mock):
    def get_title(first, key=None):
        return "You gotta lock that down"
