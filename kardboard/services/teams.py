from dateutil.relativedelta import relativedelta
from datetime import datetime

from kardboard.models.kard import Kard
from kardboard.models.states import States
from kardboard.models.team import Team, TeamList
from kardboard.util import make_start_date, make_end_date


def setup_teams(config):
    team_confs = config.get('CARD_TEAMS')
    teams = [Team(*args) for args in team_confs]
    team_list = TeamList(*teams)
    return team_list


class TeamStats(object):
    def __init__(self, team_name, exclude_classes=[]):
        self.team_name = team_name
        self.exclude_classes = exclude_classes

    def done_in_range(self, start_date, end_date):
        end_date = make_end_date(date=end_date)
        start_date = make_start_date(date=start_date)

        done = Kard.objects.filter(
            team=self.team_name,
            done_date__gte=start_date,
            done_date__lte=end_date,
            _service_class__nin=self.exclude_classes,
        )
        return done

    def wip(self):
        states = States()
        wip = Kard.objects.filter(
            team=self.team_name,
            done_date=None,
            state__in=states.in_progress,
        )
        return wip

    def wip_count(self):
        return len(self.wip())

    def weekly_throughput_ave(self, weeks=4):
        end_date = datetime.now()
        start_date = end_date - relativedelta(weeks=weeks)

        done = len(self.done_in_range(
            start_date, end_date))

        return int(round(done / float(weeks)))

    def monthly_throughput_ave(self, months=1):
        end_date = datetime.now()
        start_date = end_date - relativedelta(weeks=months * 4)

        done = len(self.done_in_range(
            start_date, end_date))

        return int(round(done / float(months)))

    def lead_time(self):
        throughput = self.weekly_throughput_ave() / 7.0
        if throughput == 0:
            return float('nan')
        return int(round(self.wip_count() / throughput))
