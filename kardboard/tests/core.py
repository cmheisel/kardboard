import unittest2


class KardboardTestCase(unittest2.TestCase):
    @property
    def class_under_test(self):
        return self._get_class()

    def make_one(self, *args, **kwargs):
        return self.class_under_test(*args, **kwargs)

    def assertEqualDateTimes(self, actual, expected):
        attrs = (
            "year",
            "month",
            "day",
            "hour",
            "minute",
        )

        if actual:
            actual_tuple = [getattr(actual, attrname)
                for attrname in attrs]
        else:
            actual_tuple = None
        if expected:
            expected_tuple = [getattr(expected, attrname)
                for attrname in attrs]
        else:
            expected_tuple = None
        self.assertEqual(actual_tuple, expected_tuple)


class ModelTestCase(KardboardTestCase):
    mongodb_name = 'kardboard_unittest'

    def setUp(self):
        from pyramid import testing
        from mongoengine import connect

        self.config = testing.setUp()
        connect(self.mongodb_name)

    def tearDown(self):
        from pyramid import testing

        from mongoengine.connection import get_connection, disconnect

        connection = get_connection()
        connection.drop_database(self.mongodb_name)
        disconnect()

        testing.tearDown()

    def make_unique_key(self):
        import random
        key = random.randint(1, 20)
        return key


class ViewTestCase(KardboardTestCase):
    def setUp(self):
        from pyramid import testing

        self.config = testing.setUp()
        self.testing = testing

    def tearDown(self):
        self.testing.tearDown()
