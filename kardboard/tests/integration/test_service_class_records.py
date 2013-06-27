import pytest

from datetime import datetime
from kardboard.tests.core import KardboardTestCase


@pytest.mark.serviceclassrecord
class ServiceClassTests(KardboardTestCase):
    def setUp(self):
        super(ServiceClassTests, self).setUp()
        lower = 5
        upper = 15
        self.config['SERVICE_CLASSES'] = {
            'Speedy': {'lower': 2, 'upper': 4, 'wip': .05, 'name': 'Speedy'},
            'Normal': {'lower': 5, 'upper': 10, 'wip': .50, 'name': 'Normal'},
            'default': {'lower': lower, 'upper': upper, 'name': 'default'},
        }


@pytest.mark.serviceclassrecord
class ServiceClassSnapshotTests(ServiceClassTests):
    def _get_target_class(self):
        from kardboard.models import ServiceClassSnapshot
        return ServiceClassSnapshot

    def _fixtures_for_test_current_struct(self):
        from kardboard.util import now
        from kardboard.util import relativedelta

        # Speedy cards
        for i in xrange(0, 5):
            k = self.make_card(
                _service_class='Speedy',
                backlog_date=now() - relativedelta(days=3),
                start_date=now() - relativedelta(days=1),
            )
            k.save()

        # Normal cards
        for i in xrange(0, 10):
            k = self.make_card(
                _service_class='Normal',
                backlog_date=now(),
                start_date=now() + relativedelta(days=10),
            )
            k.save()

        # No class cards
        for i in xrange(0, 5):
            k = self.make_card(
                backlog_date=now(),
                start_date=now() + relativedelta(days=10),
            )
            k.save()

        for i in xrange(0, 3):
            k = self.make_card(
                _service_class='Normal',
                backlog_date=now(),
                start_date=now() + relativedelta(days=8),
                done_date=now() + relativedelta(days=15)
            )
            k.save()

    def test_current_struct(self):
        self._fixtures_for_test_current_struct()

        expected = {
            'Speedy': {
                'service_class': 'Speedy',
                'wip': 5,
                'wip_percent': 5 / 20.0,
                'cycle_time_average': 1.0,
                'cards_hit_goal': 5,
                'cards_hit_goal_percent': 1.0
            },
            'Normal': {
                'service_class': 'Normal',
                'wip': 10,
                'wip_percent': 10 / 20.0,
                'cycle_time_average': 10,
                'cards_hit_goal': 10,
                'cards_hit_goal_percent': 1.0
            },
            'default': {
                'service_class': 'default',
                'wip': 5,
                'wip_percent': 5 / 20.0,
                'cycle_time_average': 10,
                'cards_hit_goal': 5,
                'cards_hit_goal_percent': 1.0
            },
        }

        Record = self._get_target_class()
        r = Record.calculate()
        self.assertEqual(expected, r.data)


class ServiceClassRecordTests(ServiceClassTests):
    def _get_target_class(self):
        from kardboard.models import ServiceClassRecord
        return ServiceClassRecord

    def _fixtures_for_test_calculate(self):
        # Speedy cards
        for i in xrange(0, 5):
            k = self.make_card(
                _service_class='Speedy',
                backlog_date=datetime(2013, 1, 1),
                start_date=datetime(2013, 1, 3),
                done_date=datetime(2013, 1, 4),
            )
            k.save()

        # Normal cards
        for i in xrange(0, 10):
            k = self.make_card(
                _service_class='Normal',
                backlog_date=datetime(2013, 1, 1),
                start_date=datetime(2013, 1, 11),
                done_date=datetime(2013, 1, 21),
            )
            k.save()

        # No class cards
        for i in xrange(0, 5):
            k = self.make_card(
                backlog_date=datetime(2013, 1, 1),
                start_date=datetime(2013, 1, 11),
                done_date=datetime(2013, 1, 26),
            )
            k.save()

        for i in xrange(0, 5):
            k = self.make_card(
                _service_class='Normal',
                backlog_date=datetime(2013, 1, 1),
                start_date=datetime(2013, 1, 9),
                done_date=datetime(2013, 1, 24),
            )
            k.save()

    def test_calculate(self):
        self._fixtures_for_test_calculate()

        expected = {
            'Speedy': {
                'service_class': 'Speedy',
                'wip': 5,
                'wip_percent': 5 / 25.0,
                'cycle_time_average': 1.0,
                'cards_hit_goal': 5,
                'cards_hit_goal_percent': 1.0
            },
            'Normal': {
                'service_class': 'Normal',
                'wip': 15,
                'wip_percent': 15 / 25.0,
                'cycle_time_average': 12.0,
                'cards_hit_goal': 10,
                'cards_hit_goal_percent': 10 / 15.0
            },
            'default': {
                'service_class': 'default',
                'wip': 5,
                'wip_percent': 5 / 25.0,
                'cycle_time_average': 15,
                'cards_hit_goal': 5,
                'cards_hit_goal_percent': 1.0
            },
        }

        Record = self._get_target_class()
        start_date = datetime(2013, 1, 1)
        end_date = datetime(2013, 1, 31)
        r = Record.calculate(start_date, end_date)
        actual = r.data

        self.assertEqual(expected, actual)
