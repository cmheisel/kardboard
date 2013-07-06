import unittest2
import pytest


@pytest.mark.teams
class TeamTests(unittest2.TestCase):
    def setUp(self):
        super(TeamTests, self).setUp()
        from kardboard.models import Team
        self.Team = Team

    def test_team_name(self):
        t = self.Team(
            name="Team 2"
        )
        assert t.name == "Team 2"

    def test_team_slug(self):
        t = self.Team(
            name="Team 1"
        )
        assert t.slug == "team-1"

    def test_team_name_stripping_right(self):
        t = self.Team(
            name="Team 3 "
        )
        assert t.name == "Team 3"

    def test_team_name_stripping_left(self):
        t = self.Team(
            name=" Team 3"
        )
        assert t.name == "Team 3"


@pytest.mark.teams
class TeamListTests(unittest2.TestCase):
    def setUp(self):
        super(TeamListTests, self).setUp()
        from kardboard.models import TeamList, Team
        self.TeamList = TeamList
        self.teams = TeamList(
            Team('Team 1'),
            Team('Team 2'),
        )

    def test_names(self):
        assert ['Team 1', 'Team 2'] == self.teams.names

    def test_mapping(self):
        expected = {
            'team-1': 'Team 1',
            'team-2': 'Team 2',
        }
        actual = self.teams.slug_name_mapping
        assert expected == actual

    def test_find_by_name(self):
        expected = self.teams[1]
        actual = self.teams.find_by_name('Team 2')
        assert expected == actual
