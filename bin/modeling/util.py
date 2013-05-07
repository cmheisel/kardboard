import dateutil

from kardboard.models.kard import Kard
from kardboard.models.reportgroup import ReportGroup
from kardboard.app import app
from kardboard.services import teams as team_service
from kardboard.util import (
    make_start_date,
    make_end_date,
)


def _get_team(team_name):
    teams = team_service.setup_teams(app.config)
    team = teams.find_by_name(team_name)
    return team


def _verify_rg(name):
    try:
        app.config.get('REPORT_GROUPS', {})[name]
        return name
    except KeyError:
        print "No team or report group with name %s" % name
        raise


def _parse_date(datestr):
    return dateutil.parser.parse(datestr)


def _convert_dates(start, end):
    start, end = _parse_date(start), _parse_date(end)
    return make_start_date(date=start), make_end_date(date=end)


def _get_cards_by_team(team, start, end):
    done_cards = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=end,
        team=team.name,
    )
    done_cards = list(done_cards)
    return done_cards


def _get_cards_by_report_group(rg_slug, start, end):
    done_cards = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=end,
    )
    done_cards = ReportGroup(rg_slug, done_cards).queryset
    done_cards = list(done_cards)
    return done_cards
