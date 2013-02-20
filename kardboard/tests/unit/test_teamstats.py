from datetime import datetime, timedelta
from math import isnan

import unittest2
import pytest
import mock

from dateutil.relativedelta import relativedelta

from kardboard.services.teams import TeamStats


@pytest.mark.teamstats
class TeamStatsTest(unittest2.TestCase):
    def setUp(self):
        super(TeamStatsTest, self).setUp()

        self.service = TeamStats('Team Foo')
        self.team = 'Team Foo'

    def tearDown(self):
        super(TeamStatsTest, self).tearDown()

    def test_done_in_range(self):
        start_date = datetime(2012, 1, 1)
        end_date = datetime(2012, 12, 31)

        with mock.patch('kardboard.services.teams.Kard') as mock_Kard:
            self.service.done_in_range(start_date, end_date)
            start_expected = datetime(2012, 1, 1, 0, 0, 0)
            end_expected = datetime(2012, 12, 31, 23, 59, 59)

            mock_Kard.objects.filter.assert_called_with(
                team=self.team,
                done_date__gte=start_expected,
                done_date__lte=end_expected,
                _service_class__nin=[],
            )

    def test_done_in_range_when_exculing_classes(self):
        service = TeamStats('Team 1', ['Urgent', 'Intangible'])

        start_date = datetime(2012, 1, 1)
        end_date = datetime(2012, 12, 31)

        with mock.patch('kardboard.services.teams.Kard') as mock_Kard:
            service.done_in_range(start_date, end_date)
            start_expected = datetime(2012, 1, 1, 0, 0, 0)
            end_expected = datetime(2012, 12, 31, 23, 59, 59)

            mock_Kard.objects.filter.assert_called_with(
                team='Team 1',
                done_date__gte=start_expected,
                done_date__lte=end_expected,
                _service_class__nin=['Urgent', 'Intangible'],
            )

    def test_wip(self):
        from kardboard.models import States
        states = States()
        with mock.patch('kardboard.services.teams.Kard') as mock_Kard:
            self.service.wip()
            mock_Kard.objects.filter.assert_called_with(
                team=self.team,
                done_date=None,
                state__in=states.in_progress,
            )

    def test_wip_count(self):
        with mock.patch.object(self.service, 'wip') as mock_wip:
            mock_wip.return_value = [i for i in range(9)]
            assert 9 == self.service.wip_count()

    def test_weekly_throughput_ave(self):
        return_value = [i for i in range(8)]
        with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
            mock_done_in_range.return_value = return_value
            result = self.service.weekly_throughput_ave()
            assert result == 2

    def test_monthly_throughput_ave(self):
        return_value = [i for i in range(8)]
        with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
            mock_done_in_range.return_value = return_value
            result = self.service.monthly_throughput_ave()
            assert result == 8

    def test_lead_time(self):
        expected = 32
        with mock.patch.object(self.service, 'wip_count') as mock_wip_count:
            mock_wip_count.return_value = 9
            with mock.patch.object(self.service, 'weekly_throughput_ave') as mock_weekly_throughput_ave:
                mock_weekly_throughput_ave.return_value = 2
                assert expected == self.service.lead_time()

    def test_cycle_times_selects_the_right_range(self):
        weeks = 4
        delta = timedelta(seconds=10)
        start_date, end_date, weeks = self.service.throughput_date_range(weeks)
        with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
                mock_done_in_range.return_value.values_list.return_value = []
                self.service.cycle_times(weeks)
                assert mock_done_in_range.called
                args, kwargs = mock_done_in_range.call_args
                self.assertAlmostEqual(start_date, args[0], delta=delta)
                self.assertAlmostEqual(end_date, args[1], delta=delta)

    def test_cycle_times_returns_scalar(self):
        with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
                mock_done_in_range.return_value.values_list.return_value = []
                self.service.cycle_times()
                mock_done_in_range.return_value.values_list.assert_called_with(
                    '_cycle_time',
                )

    def test_cycle_times_returns_only_numbers(self):
        with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
                mock_done_in_range.return_value.values_list.return_value = [1, 2, 3, None, 4]
                result = self.service.cycle_times()
                assert [1, 2, 3, 4] == result

    def test_standard_deviation(self):
        with mock.patch.object(self.service, 'cycle_times') as mock_cycle_times:
            mock_cycle_times.return_value = [13, 13, 5, 18, 0, 0, 28, 28, 2, 0, 5, 8, 5, 25]
            assert 10 == self.service.standard_deviation()

    def test_histogram(self):
        with mock.patch.object(self.service, 'cycle_times') as mock_cycle_times:
            mock_cycle_times.return_value = [1, 0, 2, 4, 10, 4, 3, 3, 7, 7, 7]
            expected = {
                0: 1,
                1: 1,
                2: 1,
                3: 2,
                4: 2,
                7: 3,
                10: 1,
            }
            assert expected == self.service.histogram()

    def test_percentile(self):
        with mock.patch.object(self.service, 'histogram') as mock_histogram:
            mock_histogram.return_value = {
                0: 1,
                1: 1,
                2: 1,
                3: 2,
                4: 2,
                7: 3,
                10: 1,
            }
            actual = self.service.percentile(.7)
            assert 7 == actual

    def test_lead_time_with_zero_throughput(self):
        with mock.patch.object(self.service, 'wip_count') as mock_wip_count:
            mock_wip_count.return_value = 9
            with mock.patch.object(self.service, 'weekly_throughput_ave') as mock_weekly_throughput_ave:
                mock_weekly_throughput_ave.return_value = 0
                assert isnan(self.service.lead_time())

    def test_oldest_card_query(self):
        with mock.patch('kardboard.services.teams.Kard') as mock_Kard:
            self.service.oldest_card_date()
            mock_Kard.objects.filter.assert_called_with(
                team=self.team,
                _service_class__nin=[],
                done_date__exists=True,
            )

    def test_oldest_card_with_no_results(self):
        with mock.patch('kardboard.services.teams.Kard.objects.first') as mock_first:
            mock_first.return_value = None
            result = self.service.oldest_card_date()
            assert None == result

    def test_throughput_date_range_defaults(self):
        end_date = datetime.now()
        start_date = end_date - relativedelta(weeks=4)

        actual = self.service.throughput_date_range()
        delta = timedelta(seconds=10)

        self.assertAlmostEqual(start_date, actual[0], delta=delta)
        self.assertAlmostEqual(end_date, actual[1], delta=delta)

    def test_throughput_date_range_with_team_less_than(self):
        delta = timedelta(seconds=10)
        with mock.patch.object(self.service, 'oldest_card_date') as mock_oldest_card_date:
            return_value = datetime.now() - relativedelta(weeks=2)
            mock_oldest_card_date.return_value = return_value
            actual = self.service.throughput_date_range(weeks=4)
            self.assertAlmostEqual(return_value, actual[0], delta=delta)

    def test_throughput_date_range_with_team_less_than_returns_weeks(self):
        with mock.patch.object(self.service, 'oldest_card_date') as mock_oldest_card_date:
            mock_oldest_card_date.return_value = datetime.now() - relativedelta(weeks=2)
            actual = self.service.throughput_date_range(weeks=4)
            assert 2 == actual[2]

    def test_throughput_date_range_with_team_greater_than(self):
        delta = timedelta(seconds=10)
        with mock.patch.object(self.service, 'oldest_card_date') as mock_oldest_card_date:
            return_value = datetime.now() - relativedelta(weeks=6)
            mock_oldest_card_date.return_value = return_value
            actual = self.service.throughput_date_range(weeks=4)
            expected = datetime.now() - relativedelta(weeks=4)
            self.assertAlmostEqual(expected, actual[0], delta=delta)

    def test_throughput_date_range_with_team_equal(self):
        delta = timedelta(seconds=10)
        with mock.patch.object(self.service, 'oldest_card_date') as mock_oldest_card_date:
            return_value = datetime.now() - relativedelta(weeks=4)
            mock_oldest_card_date.return_value = return_value
            actual = self.service.throughput_date_range(weeks=4)
            expected = datetime.now() - relativedelta(weeks=4)
            self.assertAlmostEqual(expected, actual[0], delta=delta)

    def test_throughput_date_range_less_than(self):
        with mock.patch.object(self.service, 'oldest_card_date') as mock_oldest_card_date:
            mock_oldest_card_date.return_value = datetime.now() - relativedelta(weeks=2)
            with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
                return_value = [i for i in range(8)]
                mock_done_in_range.return_value = return_value
                result = self.service.weekly_throughput_ave()
                assert result == 4

    def test_monthly_throughput_date_range_less_than(self):
        with mock.patch.object(self.service, 'oldest_card_date') as mock_oldest_card_date:
            mock_oldest_card_date.return_value = datetime.now() - relativedelta(weeks=6)
            with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
                return_value = [i for i in range(8)]
                mock_done_in_range.return_value = return_value
                result = self.service.monthly_throughput_ave(months=3)
                assert result == 4
