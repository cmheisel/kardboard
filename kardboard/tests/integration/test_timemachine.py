import datetime

from kardboard.tests.core import KardboardTestCase


class KardTimeMachineTests(KardboardTestCase):
    def setUp(self):
        super(KardTimeMachineTests, self).setUp()
        self._set_up_data()

    def _get_target_class(self):
        return self._get_card_class()

    def _make_one(self, **kwargs):
        return self.make_card(**kwargs)

    def _set_up_data(self):
        klass = self._get_target_class()

        # Simulate creating 5 cards and moving
        # some forward
        backlog_date = datetime.datetime(
            year=2011, month=5, day=30)
        for i in xrange(0, 5):
            c = self._make_one(backlog_date=backlog_date)
            c.save()

        cards = klass.objects.all()[:2]
        for c in cards:
            c.start_date = backlog_date.replace(day=31)
            c.save()

        for c in cards:
            c.done_date = backlog_date.replace(month=6, day=2)
            c.save()

    def test_time_machine(self):
        klass = self._get_target_class()

        backlogged_day = datetime.datetime(
            year=2011, month=5, day=30)
        started_2_day = datetime.datetime(
            year=2011, month=5, day=31)
        finished_2_day = datetime.datetime(
            year=2011, month=6, day=2)

        today = datetime.datetime(
            year=2011, month=6, day=12)

        expected = 2
        actual = klass.in_progress(today)
        self.assertEqual(expected, actual.count())

        expected = 0
        actual = klass.in_progress(backlogged_day)
        self.assertEqual(expected, actual.count())

        expected = 2
        actual = klass.in_progress(started_2_day)
        self.assertEqual(expected, actual.count())

        expected = 2
        actual = klass.in_progress(finished_2_day)
        self.assertEqual(expected, actual.count())
