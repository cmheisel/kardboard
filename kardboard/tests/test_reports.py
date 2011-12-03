import datetime
from dateutil.relativedelta import relativedelta
from copy import deepcopy

from mock import patch

from kardboard.tests.core import KardboardTestCase, DashboardTestCase


class ReportTests(DashboardTestCase):
    base_url = '/reports'


class ReportGroupTests(KardboardTestCase):
    def setUp(self):
        super(ReportGroupTests, self).setUp()
        from kardboard.app import app
        self._orig_groups = deepcopy(
            app.config.get('REPORT_GROUPS', {})
        )

        app.config['REPORT_GROUPS'] = {
            'ops': (('Ops',), 'Ops'),
            'dev': (('Team 1', 'Team 2', 'Team 3'), 'Development'),
        }

        self._set_up_fixtures()

    def _set_up_fixtures(self):
        for i in xrange(0, 3):
            k = self.make_card()
            k.team = 'Team 1'
            k.save()

        for i in xrange(0, 3):
            k = self.make_card()
            k.team = 'Team 2'
            k.save()

        for i in xrange(0, 3):
            k = self.make_card()
            k.team = 'Team 3'
            k.save()

        for i in xrange(0, 3):
            k = self.make_card()
            k.team = 'Ops'
            k.save()

    def tearDown(self):
        from kardboard.app import app
        app.config['REPORT_GROUPS'] = self._orig_groups
        Kard = self._get_card_class()
        Kard.objects.all().delete()

    def _get_target_klass(self):
        from kardboard.models import ReportGroup
        return ReportGroup

    def test_report_group_all(self):
        Kard = self._get_card_class()
        klass = self._get_target_klass()
        queryset = Kard.objects

        orig_count = len(queryset)

        report_group = klass('all', queryset)

        self.assertEqual(orig_count, len(report_group.queryset))

    def test_report_group_ops(self):
        Kard = self._get_card_class()
        klass = self._get_target_klass()

        report_group = klass('ops', Kard.objects)

        self.assertEqual(3, len(report_group.queryset))

    def test_report_group_dev(self):
        Kard = self._get_card_class()
        klass = self._get_target_klass()

        report_group = klass('dev', Kard.objects)

        self.assertEqual(9, len(report_group.queryset))


class ChartIndexTests(ReportTests):
    def _get_target_url(self):
        return '%s/' % (self.base_url, )

    def test_chart_index(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)

        expected = [
            '/all/done/',
            '/all/throughput/',
            '/all/cycle/distribution/',
            '/all/cycle/',
            '/all/flow/',
        ]
        for url in expected:
            self.assertIn(url, res.data)


class DonePageTests(DashboardTestCase):
    def _get_target_url(self, months=None):
        base_url = '/reports/all/done/'
        if months:
            base_url = base_url + "%s/" % months
        return base_url

    def test_done_page(self):
        rv = self.app.get(self._get_target_url(months=12))
        self.assertEqual(200, rv.status_code)

        done = self.Kard.objects.done()

        for c in done:
            self.assertIn(c.key, rv.data)


class ThroughputChartTests(KardboardTestCase):
    def _get_target_url(self, months=None):
        base_url = '/reports/all/throughput/'
        if months:
            base_url = base_url = "%s/" % months
        return base_url

    def test_throughput(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)


class CycleDistributionTests(KardboardTestCase):
    def _get_target_url(self, months=None):
        base_url = '/reports/all/cycle/distribution/'
        if months:
            base_url = base_url = "%s/" % months
        return base_url

    def setUp(self):
        super(CycleDistributionTests, self).setUp()

        for i in xrange(0, 30):
            today = datetime.datetime.now()
            backlog_date = today - relativedelta(days=2 + i)
            start_date = today - relativedelta(days=1 + i)
            done_date = today
            k = self.make_card(
                backlog_date=backlog_date,
                start_date=start_date,
                done_date=done_date,)
            k.save()

    def test_distribution(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)


class CycleTimeHistoryTests(DashboardTestCase):
    def setUp(self):
        super(CycleTimeHistoryTests, self).setUp()
        self._set_up_records()

    def _get_target_url(self, months=None, date=None):
        base_url = '/reports/all/cycle/'
        if months:
            base_url = base_url + "%s/" % months
        if date:
            base_url = base_url + "from/%s/%s/%s/" % \
                (date.year, date.month, date.day)
        return base_url

    def test_cycle(self):
        date = datetime.datetime(year=2011, month=7, day=1)
        end_date = date - relativedelta(months=3)
        target_url = self._get_target_url(date=date)
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)

        expected = end_date.strftime("%m/%d/%Y")
        self.assertIn(expected, res.data)


class CumulativeFlowTests(DashboardTestCase):
    def setUp(self):
        super(CumulativeFlowTests, self).setUp()
        self._set_up_records()
        klass = self._get_record_class()
        self.today = klass.objects.order_by('-date').first().date

        self.patcher = patch('kardboard.util.now', lambda: self.today)
        self.mock_now = self.patcher.start()

    def tearDown(self):
        super(CumulativeFlowTests, self).tearDown()
        self.patcher.stop()

    def _get_target_url(self, months=None):
        base_url = '/reports/all/flow/'
        if months:
            base_url = base_url = "%s/" % months
        return base_url

    def test_cum_flow(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)
