from datetime import datetime

import unittest2
import pytest
import mock

from kardboard.services.teams import TeamStats

from kardboard.util import isnan


@pytest.mark.teamstats
class TeamStatsTest(unittest2.TestCase):
    def setUp(self):
        super(TeamStatsTest, self).setUp()

        self.service = TeamStats('Team 1')
        self.team = 'Team 1'

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

    def test_lead_time_with_zero_throughput(self):
        with mock.patch.object(self.service, 'wip_count') as mock_wip_count:
            mock_wip_count.return_value = 9
            with mock.patch.object(self.service, 'weekly_throughput_ave') as mock_weekly_throughput_ave:
                mock_weekly_throughput_ave.return_value = 0
                assert isnan(self.service.lead_time())

