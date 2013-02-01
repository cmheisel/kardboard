import unittest2
import pytest


@pytest.mark.teams
class TeamServiceTests(unittest2.TestCase):

    def setUp(self):
        super(TeamServiceTests, self).setUp()
        from kardboard.services import teams
        self.service = teams

    def test_setup_teams(self):
        config = {
            'CARD_TEAMS': [
                ('Team 1', 100),
                ('Team 2', 20),
            ]
        }

        teams = self.service.setup_teams(config)
        assert 2 == len(teams)

    def test_setup_teams_returns_team_objects(self):
        config = {
            'CARD_TEAMS': [
                ('Team 1', 100),
                ('Team 2', 20),
            ]
        }

        teams = self.service.setup_teams(config)
        assert hasattr(teams[0], 'slug')

    def test_setup_teams_with_mixed_wip(self):
        config = {
            'CARD_TEAMS': [
                ('Team 1', 100),
                ('Team 2', ),
            ]
        }

        teams = self.service.setup_teams(config)
        assert 0 == teams[1].wip_limit
