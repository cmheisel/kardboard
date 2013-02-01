from kardboard.models.team import Team, TeamList


def setup_teams(config):
    team_names = config.get('CARD_TEAMS')
    teams = [Team(n) for n in team_names]
    team_list = TeamList(*teams)
    return team_list
