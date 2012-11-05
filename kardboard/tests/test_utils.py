import unittest2


class UtilTests(unittest2.TestCase):

    def test_delta_in_hours(self):
        from datetime import datetime
        from ..util import delta_in_hours

        dt1 = datetime(2012, 11, 4, 12, 0, 0)
        dt2 = datetime(2012, 11, 4, 13, 0, 0)

        actual = delta_in_hours(dt2 - dt1)
        self.assertEqual(1, actual)
