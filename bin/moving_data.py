from dateutil.relativedelta import relativedelta
from kardboard.models import Kard, ReportGroup, FlowReport, DailyRecord
from kardboard.util import make_start_date, make_end_date


def parse_date(datestr):
    from dateutil import parser
    return parser.parse(datestr)


def daily_throughput_average(stop, weeks=4):
    start = (stop - relativedelta(days=weeks * 7)) + relativedelta(days=1)
    start = make_start_date(date=start)

    query = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=stop,)

    kards = list(ReportGroup('dev', query).queryset)
    return len(kards) / float(weeks * 7)


def find_wip(stop):
    sl = FlowReport.objects.get(
        date=make_end_date(date=stop),
        group='dev',
    )

    exclude = [u'Backlog', u'Done', ]
    wip = 0
    for state, count in sl.state_counts.items():
        if state not in exclude:
            wip += count

    return wip


def find_cycle_time_ave(stop):
    dr = DailyRecord.objects.get(
        date=make_end_date(date=stop),
        group='dev',
    )

    return dr.moving_cycle_time


def moving_data(start, stop):
    query = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=stop,)

    kards = list(ReportGroup('dev', query).queryset)
    features = [k for k in kards if k.is_card]
    defects = [k for k in kards if not k.is_card]

    wip = find_wip(stop)
    tpa = daily_throughput_average(stop)
    little_law = wip / float(tpa)

    cycle_time_ave = find_cycle_time_ave(stop)

    data = {
        'start': start,
        'stop': stop,
        'features': len(features),
        'bugfixes': len(defects),
        'little_law': round(little_law),
        'cycle_time_ave': round(cycle_time_ave),
        'wip': wip,
    }
    return data


def print_data(data):
    print "%s - %s\nF: %s\tB: %s\tL: %s\tC: %s\tW: %s" % (
        data['start'],
        data['stop'],
        data['features'],
        data['bugfixes'],
        data['little_law'],
        data['cycle_time_ave'],
        data['wip'],
    )


def weekly_moving_data(start):
    start = parse_date(start)
    stop = start + relativedelta(days=6)

    start = make_start_date(date=start)
    stop = make_end_date(date=stop)
    return moving_data(start, stop)


if __name__ == "__main__":
    import sys
    data = weekly_moving_data(sys.argv[1])
    print_data(data)
