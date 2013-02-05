from datetime import datetime

import unittest2
import pytest
import mock

from kardboard.services.teams import TeamStats


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

    def test_weekly_throughput_ave(self):
        return_value = [i for i in range(8)]
        with mock.patch.object(self.service, 'done_in_range') as mock_done_in_range:
            mock_done_in_range.return_value = return_value
            result = self.service.weekly_throughput_ave()
            assert result == 2.0
