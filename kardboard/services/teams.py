from dateutil.relativedelta import relativedelta
from datetime import datetime

from kardboard.models import Kard
from kardboard.models.team import Team, TeamList
from kardboard.util import make_start_date, make_end_date


def setup_teams(config):
    team_confs = config.get('CARD_TEAMS')
    teams = [Team(*args) for args in team_confs]
    team_list = TeamList(*teams)
    return team_list

class TeamStats(object):
    def __init__(self, team_name):
        self.team_name = team_name

    def done_in_range(self, start_date, end_date):

        end_date = make_end_date(date=end_date)
        start_date = make_start_date(date=start_date)

        done = Kard.objects.filter(
            team=self.team_name,
            done_date__gte=start_date,
            done_date__lte=end_date,
        )
        return done

    def weekly_throughput_ave(self, weeks=4):
        end_date = datetime.now()
        start_date = end_date - relativedelta(weeks=weeks)

        done = len(self.done_in_range(
            start_date, end_date))

        return done / float(weeks)
