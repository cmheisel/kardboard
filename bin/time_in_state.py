"""
For a team, for a period of weeks, for each service class and for them all, show how long cards (not defects) spend in each state on average.
"""
from datetime import datetime

from dateutil.relativedelta import relativedelta

from kardboard.app import app
from kardboard.models.reportgroup import ReportGroup
from kardboard.models.kard import Kard
from kardboard.models.statelog import StateLog
from kardboard.models.states import States
from kardboard.services import teams as team_service
from kardboard.util import make_start_date, make_end_date, average


def _get_team(team_name):
    teams = team_service.setup_teams(app.config)
    team = teams.find_by_name(team_name)
    return team


def _get_time_range(weeks, start=None, end=None):
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - relativedelta(weeks=weeks)
    return make_start_date(date=start), make_end_date(date=end)


def _get_cards(team, start, end):
    # We need cards that are done
    # Plus cards that are in progress
    done_cards = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=end,
        team=team.name,
    )
    done_cards = list(done_cards)
    return done_cards


def _get_cards_by_report_group(rg_slug, start, end):
    # We need cards that are done
    # Plus cards that are in progress
    done_cards = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=end,
    )
    done_cards = ReportGroup(rg_slug, done_cards).queryset
    done_cards = list(done_cards)
    return done_cards


def _get_card_logs(card):
    return StateLog.objects.filter(card=card)


def _sum_card_history(history):
    data = {}
    for state, logs in history.items():
        state_sum = 0
        for log in logs:
            state_sum += log.duration
        data[state] = state_sum
    return data


def collect_card_state_time(cards):
    data = {}
    for card in cards:
        logs = _get_card_logs(card)
        card_history = {}
        for log in logs:
            hist = card_history.get(log.state, [])
            hist.append(log)
            card_history[log.state] = hist
        card_history = _sum_card_history(card_history)
        for state, state_sum in card_history.items():
            state_data = data.get(state, [])
            state_data.append(state_sum)
            data[state] = state_data

    for state, hour_list in data.items():
        data[state] = [float(h / 24.0) for h in hour_list]
    return data


def card_state_averages(card_state_time):
    averages = {}
    for state, day_data in card_state_time.items():
        averages[state] = average(day_data)
    return averages


def _verify_rg(name):
    try:
        app.config.get('REPORT_GROUPS', {})[name]
        return name
    except KeyError:
        print "No team or report group with name %s" % name
        raise


def parse_date(datestr):
    from dateutil import parser
    return parser.parse(datestr)


def report_suite(name, weeks=None, start=None, end=None):
    start, end = _get_time_range(weeks, start, end)
    try:
        team = _get_team(name)
        cards = _get_cards(team, start, end)
    except ValueError:
        rg_slug = _verify_rg(name)
        cards = _get_cards_by_report_group(rg_slug, start, end)

    card_state_time = collect_card_state_time(cards)
    averages = card_state_averages(card_state_time)

    states = States()
    unknown_states = [s for s in averages.keys() if s not in states]
    for state in states:
        print "%s\t%s" % (
            state,
            averages.get(state, "N/A")
        )
    for state in unknown_states:
        print "UNUSED %s\t %s" % (
            state,
            averages.get(state, "N/A")
        )

    print "Cards\t %s" % (
        len([c for c in cards if c.is_card])
    )
    print "Defects\t %s" % (
        len([c for c in cards if c.is_card is False])
    )


if __name__ == "__main__":
    import sys
    team_name = sys.argv[1]
    start_date = parse_date(sys.argv[2])
    end_date = parse_date(sys.argv[3])
    report_suite(team_name, None, start_date, end_date)
