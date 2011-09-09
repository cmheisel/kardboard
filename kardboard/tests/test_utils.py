import datetime

import unittest2


class UtilTests(unittest2.TestCase):
    def test_business_days(self):
        from kardboard.util import business_days_between

        wednesday = datetime.datetime(year=2011, month=6, day=1)
        next_wednesday = datetime.datetime(year=2011, month=6, day=8)
        result = business_days_between(wednesday, next_wednesday)
        self.assertEqual(result, 5)

        aday = datetime.datetime(year=2011, month=6, day=1)
        manydayslater = datetime.datetime(year=2012, month=6, day=1)
        result = business_days_between(aday, manydayslater)
        self.assertEqual(result, 262)

    def test_month_range(self):
        from kardboard.util import month_range

        today = datetime.datetime(year=2011, month=6, day=12)
        start, end = month_range(today)
        self.assertEqual(6, start.month)
        self.assertEqual(1, start.day)
        self.assertEqual(2011, start.year)

        self.assertEqual(6, end.month)
        self.assertEqual(30, end.day)
        self.assertEqual(2011, end.year)

    def test_week_range(self):
        from kardboard.util import week_range
        today = datetime.datetime(year=2011, month=5, day=12)
        start, end = week_range(today)

        self.assertEqual(5, start.month)
        self.assertEqual(8, start.day)
        self.assertEqual(2011, start.year)

        self.assertEqual(5, end.month)
        self.assertEqual(14, end.day)
        self.assertEqual(2011, end.year)

        today = datetime.datetime(year=2011, month=6, day=5)
        start, end = week_range(today)
        self.assertEqual(6, start.month)
        self.assertEqual(5, start.day)
        self.assertEqual(2011, start.year)

        self.assertEqual(6, end.month)
        self.assertEqual(11, end.day)
        self.assertEqual(2011, end.year)