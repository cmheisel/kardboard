import csv
from collections import namedtuple

from kardboard.app import app
from kardboard.models.kard import Kard
from kardboard.models.reportgroup import ReportGroup
from kardboard.services import teams as team_service
from kardboard.util import make_start_date, make_end_date, slugify, now

from time_in_state import collect_card_state_time


def parse_date(datestr):
    from dateutil import parser
    return parser.parse(datestr)


def _broke_limit(card):
    if card.cycle_time and card.cycle_time > card.service_class['upper']:
        return (card.cycle_time, card.service_class['upper'])
    elif card.current_cycle_time() > card.service_class['upper']:
        return (card.current_cycle_time(), card.service_class['upper'])
    return (None, None)


def _get_team(team_name):
    teams = team_service.setup_teams(app.config)
    team = teams.find_by_name(team_name)
    return team


def _get_team_qs(team, start):
    qs = Kard.objects.filter(
        start_date__gte=start,
        team=team.name,
    )
    return qs


def _get_report_group_qs(rg_slug, start):
    # We need cards that are done
    # Plus cards that are in progress
    cards = Kard.objects.filter(
        start_date__gte=start,
    )
    qs = ReportGroup(rg_slug, cards).queryset
    return qs


def _verify_rg(name):
    try:
        app.config.get('REPORT_GROUPS', {})[name]
        return name
    except KeyError:
        print "No team or report group with name %s" % name
        raise


def _get_cards(team_or_rg_name, start_date):
    try:
        team = _get_team(team_or_rg_name)
        qs = _get_team_qs(team, start_date)
    except ValueError:
        rg_slug = _verify_rg(team_or_rg_name)
        qs = _get_report_group_qs(rg_slug, start_date)
    return list(qs)


def _hit_due_date(card):
    if card.due_date is None:
        return ''

    due_date = make_end_date(date=card.due_date)
    if card.done_date is None:
        done_date = make_end_date(date=now())
    else:
        done_date = make_end_date(date=card.done_date)
    return done_date <= due_date


def _hit_sla(card):
    if card.cycle_vs_goal <= 0:
        return True
    else:
        return False


def _format_date_or_empty(date):
    if date is None:
        return ''
    return date.strftime('%Y-%m-%d')


def _card_type(card):
    if card.is_card:
        return 'Card'
    else:
        return 'Bug'


def _get_state_time(name, card):
    card_times = collect_card_state_time([card, ])
    state_time = card_times.get(name, ['', ])[0]
    return state_time


def _time_in_otis(card):
    return _get_state_time('Build to OTIS', card)


def _time_wait_qa(card):
    return _get_state_time('Ready: Testing', card)


def _time_in_qa(card):
    return _get_state_time('Testing', card)


def _time_building(card):
    return _get_state_time('Building', card)


def _time_elabo(card):
    return _get_state_time('Elaborating', card)


def started_after_report(team_or_rg_name, start_date):
    start_date = make_start_date(date=start_date)
    cards = _get_cards(team_or_rg_name, start_date)

    columns = (
        'key',
        'team',
        'service_class',
        'type',
        'start_date',
        'done_date',
        'due_date',
        'cycle_time',
        'is_wip',
        'hit_due_date',
        'hit_sla',
        'time_in_otis',
        'time_wait_qa',
        'time_in_qa',
        'time_building',
        'time_elabo',
    )

    Row = namedtuple('Row', ' '.join(columns))
    rows = []
    for c in cards:
        row = Row(
            key=c.key,
            team=c.team,
            service_class=c.service_class['name'],
            type=_card_type(c),
            start_date=_format_date_or_empty(c.start_date),
            done_date=_format_date_or_empty(c.done_date),
            due_date=_format_date_or_empty(c.due_date),
            cycle_time=c.cycle_time or c.current_cycle_time(),
            is_wip=(c.done_date is None),
            hit_due_date=_hit_due_date(c),
            hit_sla=_hit_sla(c),
            time_in_otis=_time_in_otis(c),
            time_wait_qa=_time_wait_qa(c),
            time_in_qa=_time_in_qa(c),
            time_building=_time_building(c),
            time_elabo=_time_elabo(c),
        )
        rows.append(row)

    rows.insert(0, columns)

    report_filename = "%s_%s.csv" % (
        start_date.strftime('%Y-%m-%d'),
        slugify(team_or_rg_name)
    )

    writer = csv.writer(
        open(report_filename, 'w'),
    )
    writer.writerows(rows)


if __name__ == "__main__":
    import sys
    start_date = parse_date(sys.argv[1])
    team_name = sys.argv[2]
    started_after_report(team_name, start_date)
