from collections import defaultdict

from time_in_state import (
    parse_date,
    _get_time_range,
    _get_team,
    _verify_rg,
)

from kardboard.models.reportgroup import ReportGroup
from kardboard.models.kard import Kard
from kardboard.util import average


def histogram(data):
    d = defaultdict(int)
    for data_point in data:
        d[data_point] += 1
    return dict(d)


def _get_cards(team, start, end):
    # We need cards that are done
    # Plus cards that are in progress
    done_cards = Kard.objects.filter(
        done_date__exists=True,
        start_date__gte=start,
        start_date__lte=end,
        team=team.name,
    )
    done_cards = list(done_cards)

    wip_cards = Kard.objects.filter(
        start_date__gte=start,
        start_date__lte=end,
        done_date__exists=False,
        team=team.name,
    )
    wip_cards = list(wip_cards)
    return (done_cards, wip_cards)


def _get_cards_by_report_group(rg_slug, start, end):
    # We need cards that are done
    # Plus cards that are in progress
    done_cards = Kard.objects.filter(
        done_date__exists=True,
        start_date__gte=start,
        start_date__lte=end,
        _service_class="3 - Standard",
    )
    done_cards = ReportGroup(rg_slug, done_cards).queryset
    done_cards = list(done_cards)

    wip_cards = Kard.objects.filter(
        start_date__gte=start,
        start_date__lte=end,
        done_date__exists=False,
        _service_class="3 - Standard",
    )
    wip_cards = ReportGroup(rg_slug, wip_cards).queryset
    wip_cards = list(wip_cards)

    return (done_cards, wip_cards)


def report_suite(name, start, end):
    start, end = _get_time_range(None, start, end)
    try:
        team = _get_team(name)
        done, wip = _get_cards(team, start, end)
    except ValueError:
        rg_slug = _verify_rg(name)
        done, wip = _get_cards_by_report_group(rg_slug, start, end)

    done = [k for k in done if k.is_card]
    wip = [k for k in done if k.is_card]

    for k in done:
        print "%s - %s - %s" % (k.key, k.cycle_time, k._service_class)

    cycle_times = [c.cycle_time for c in done]

    hist = histogram(cycle_times)

    print "Sample size: %s" % len(cycle_times)
    print "Average: %s" % average(cycle_times)
    for k, v in hist.items():
        print "%s\t%s" % (k, v)


if __name__ == "__main__":
    import sys
    team_name = sys.argv[1]
    start_date = parse_date(sys.argv[2])
    end_date = parse_date(sys.argv[3])
    report_suite(team_name, start_date, end_date)
