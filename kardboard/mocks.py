from mock import Mock


class MockJIRAHelper(Mock):
    def get_title(self, key):
        return "You gotta lock that down"
