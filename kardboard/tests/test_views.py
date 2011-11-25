import datetime

from mock import patch
from dateutil.relativedelta import relativedelta

from kardboard.util import slugify
from kardboard.tests.core import KardboardTestCase, DashboardTestCase


class StateTests(DashboardTestCase):
    def _get_target_url(self, state=None):
        base_url = '/'
        return base_url

    def test_state_page(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)


class TeamTests(DashboardTestCase):
    def _get_target_url(self, team):
        team_slug = slugify(team)
        return '/team/%s/' % team_slug

    def test_team_page(self):
        res = self.app.get(self._get_target_url(self.team1))
        self.assertEqual(200, res.status_code)


class DetailPageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/card/%s/' % self.card.key

    def setUp(self):
        super(DetailPageTests, self).setUp()
        self.card = self._get_card_class().objects.first()
        self.response = self.app.get(self._get_target_url())
        self.assertEqual(200, self.response.status_code)

    def test_data(self):
        expected_values = [
            self.card.title,
            self.card.key,
            self.card.backlog_date.strftime("%m/%d/%Y"),
            "Start date:",
            "Done date:",
            "/card/%s/edit/" % self.card.key,
            "/card/%s/delete/" % self.card.key,
        ]
        for v in expected_values:
            self.assertIn(v, self.response.data)


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


class QuickJumpTests(DashboardTestCase):
    def _get_target_url(self, key):
        return '/quick/?key=%s' % (key, )

    def test_quick_existing(self):
        key = self.Kard.objects.first().key

        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)

        expected = "/card/%s/" % (key, )
        self.assertIn(expected, res.headers['Location'])

    def test_quick_case_insenitive(self):
        key = self.Kard.objects.first().key
        lower_key = key.lower()

        res = self.app.get(self._get_target_url(lower_key))
        self.assertEqual(302, res.status_code)

        expected = "/card/%s/" % (key.upper(), )
        self.assertIn(expected, res.headers['Location'])

    def test_quick_add(self):
        key = "CMSCMSCMS-127"
        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)
        expected = "/card/add/?key=%s" % (key, )
        self.assertIn(expected, res.headers['Location'])


class ExportTests(KardboardTestCase):
    def _get_target_url(self):
        return '/card/export/'

    def setUp(self):
        super(ExportTests, self).setUp()
        for i in xrange(0, 10):
            c = self.make_card()
            c.save()

    def test_csv(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn("text/plain", res.headers['Content-Type'])

        Kard = self._get_card_class()
        for k in Kard.objects.all():
            self.assertIn(k.key, res.data)


class RobotsTests(KardboardTestCase):
    def _get_target_url(self):
        return '/robots.txt'

    def test_robots(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)


class PersonTests(KardboardTestCase):
    def setUp(self):
        super(PersonTests, self).setUp()
        self.person = self.make_person()
        self.person.save()

    def _get_target_url(self):
        return '/person/%s/' % self.person.name

    def test_person(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)
