from dateutil.relativedelta import relativedelta
from kardboard.models import Kard, ReportGroup, FlowReport, DailyRecord
from kardboard.util import make_start_date, make_end_date, average, standard_deviation


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
    try:
        dr = DailyRecord.objects.get(
            date=make_end_date(date=stop),
            group='dev',
        )
    except DailyRecord.DoesNotExist:
        print "No Daily Record: %s %s" % ('dev', make_end_date(date=stop))
        raise

    return dr.moving_cycle_time


def moving_data(report_group_slug, start, stop):
    query = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=stop,)

    kards = list(ReportGroup(report_group_slug, query).queryset)
    features = [k for k in kards if k.is_card]
    defects = [k for k in kards if not k.is_card]
    over_sla = [k for k in kards if k.cycle_time > k.service_class['upper']]
    card_cycle_ave = average([k.cycle_time for k in kards]) or 0
    card_stddev = standard_deviation([k.cycle_time for k in kards]) or 0

    wip = find_wip(stop)
    tpa = daily_throughput_average(stop)
    little_law = wip / float(tpa)

    cycle_time_ave = find_cycle_time_ave(stop)

    data = {
        'start': start,
        'stop': stop,
        'features': len(features),
        'bugfixes': len(defects),
        'little_law': int(round(little_law)),
        'cycle_time_ave': int(round(cycle_time_ave)),
        'wip': wip,
        'cycle_average': int(round(card_cycle_ave)),
        'stddev': int(round(card_stddev)),
        'over_sla': len(over_sla),
    }
    return data


def print_data(data):
    print "%s - %s" % (data['start'], data['stop'],)
    print "Feat: %s" % data['features']
    print "Bugs: %s" % data['bugfixes']
    print "Lead: %s" % data['little_law']
    print "Cycl: %s" % data['cycle_time_ave']
    print " WIP: %s" % data['wip']
    print "oSLA: %s" % data['over_sla']
    print "fCyc: %s" % data['cycle_average']
    print "fStd: %s" % data['stddev']


def weekly_moving_data(report_group_slug, start):
    start = parse_date(start)
    stop = start + relativedelta(days=6)

    start = make_start_date(date=start)
    stop = make_end_date(date=stop)
    return moving_data(report_group_slug, start, stop)


if __name__ == "__main__":
    import sys
    try:
        data = weekly_moving_data(sys.argv[1], sys.argv[2])
    except IndexError:
        print "{report_group_slug} {week_start_date}"
        raise
    print_data(data)
