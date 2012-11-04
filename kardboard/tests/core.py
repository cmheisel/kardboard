import unittest2

from pyramid import testing


class KardboardTestCase(unittest2.TestCase):
    pass


class ViewTestCase(KardboardTestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.testing = testing

    def tearDown(self):
        testing.tearDown()
