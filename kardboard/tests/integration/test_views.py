from copy import deepcopy

import py

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


@py.test.mark.funnel
class FunnelTests(DashboardTestCase):
    def setUp(self):
        super(FunnelTests, self).setUp()
        self.old_config = deepcopy(self.config)
        self.config['CARD_STATES'] = (
            'Backlog',
            'In Progress',
            'Deploy',
            'Done',
        )

        self.config['FUNNEL_VIEWS'] = {
            'Deploy': 2,
        }

        nondefault_keys = [
            'BACKLOG_STATE',
            'START_STATE',
            'DONE_STATE',
        ]
        for key in nondefault_keys:
            if key in self.config.keys():
                del(self.config[key])

    def tearDown(self):
        self.config = deepcopy(self.old_config)

    def _get_target_url(self, state):
        state_slug = slugify(state)
        return '/funnel/%s/' % state_slug

    def test_funnel_get(self):
        res = self.app.get(self._get_target_url('Deploy'))
        self.assertEqual(200, res.status_code)

    def test_funnel_404(self):
        res = self.app.get(self._get_target_url('In Progress'))
        self.assertEqual(404, res.status_code)

    def test_funnel_404_if_unknown_state(self):
        res = self.app.get(self._get_target_url('Foo Bar'))
        self.assertEqual(404, res.status_code)


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
            "/card/%s/edit/" % self.card.key,
            "/card/%s/delete/" % self.card.key,
        ]
        for v in expected_values:
            self.assertIn(v, self.response.data)


class QuickJumpTests(DashboardTestCase):
    def _get_target_url(self, key):
        return '/quick/?key=%s' % (key, )

    def test_quick_existing(self):
        key = self.Kard.objects.first().key

        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)

        expected = "/card/%s/" % (key, )
        self.assertIn(expected, res.headers['Location'])

    def test_quick_stripping(self):
        """The value passed to the quick
        view should be stripped of leading and
        trailing white space."""
        key = self.Kard.objects.first().key
        key = "  %s  " % (key, )

        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)

        expected = "/card/%s/" % (key.strip(), )
        self.assertIn(expected, res.headers['Location'])

        key = "CMSCMSCMS-127  "
        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)
        stripped_key = key.strip()
        expected = "/card/add/?key=%s" % (stripped_key, )
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
