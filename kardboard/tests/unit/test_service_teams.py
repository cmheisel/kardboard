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
                'Team 1',
                'Team 2',
            ]
        }

        teams = self.service.setup_teams(config)
        assert 2 == len(teams)

    def test_setup_teams_returns_team_objects(self):
        config = {
            'CARD_TEAMS': [
                'Team 1',
                'Team 2',
            ]
        }

        teams = self.service.setup_teams(config)
        assert hasattr(teams[0], 'slug')
