"""
Tests for the deprecated dashboard/overview views.
"""
import datetime

from kardboard.tests.core import DashboardTestCase


class HomepageTests(DashboardTestCase):
    def _get_target_url(self):
        # We have to specify a day, because otherwise just / would
        # be whatever day it is when you run the tests

        return '/overview/%s/%s/%s/' % (self.year, self.month, self.day)

    def test_wip(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)
        date = datetime.datetime(self.year, self.month, self.day)

        expected_cards = list(self.Kard.backlogged(date)) + \
            list(self.Kard.in_progress(date))

        for c in expected_cards:
            self.assertIn(c.key, rv.data)


class MonthPageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/overview/%s/%s/' % (self.year, self.month)

    def test_wip(self):
        from kardboard.util import month_range

        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        date = datetime.datetime(self.year, self.month, self.day)
        start, date = month_range(date)
        expected_cards = self.Kard.in_progress(date)

        for c in expected_cards:
            self.assertIn(c.key, rv.data)

        expected = """<p class="value">%s</p>""" % expected_cards.count()
        self.assertIn(expected, rv.data)

    def test_done_month_metric(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        done_month = self.Kard.objects.done_in_month(
            year=self.year, month=self.month)

        expected = """<p class="value">%s</p>""" % done_month.count()
        self.assertIn(expected, rv.data)

    def test_cycle_time_metric(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        cycle_time = self.Kard.objects.moving_cycle_time(
            year=self.year, month=self.month)

        expected = """<p class="value">%s</p>""" % cycle_time
        self.assertIn(expected, rv.data)


class DayPageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/overview/%s/%s/%s/' % (self.year, self.month, self.day)

    def test_done_in_week_metric(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        done = self.Kard.objects.done_in_week(
            year=self.year, month=self.month, day=self.day).count()

        expected = """<p class="value">%s</p>""" % done
        self.assertIn(expected, rv.data)
