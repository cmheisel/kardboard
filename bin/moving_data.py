from dateutil.relativedelta import relativedelta
from kardboard.models import Kard, ReportGroup, FlowReport, DailyRecord
from kardboard.util import make_start_date, make_end_date, average, standard_deviation


def parse_date(datestr):
    from dateutil import parser
    return parser.parse(datestr)


def daily_throughput_average(report_group_slug, stop, weeks=4):
    start = (stop - relativedelta(days=weeks * 7)) + relativedelta(days=1)
    start = make_start_date(date=start)

    query = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=stop,)

    kards = list(ReportGroup(report_group_slug, query).queryset)
    return len(kards) / float(weeks * 7)


def find_flow_report(report_group_slug, stop):
    sl = FlowReport.objects.get(
        date=make_end_date(date=stop),
        group=report_group_slug,
    )
    return sl


def find_wip(report_group_slug, stop):
    try:
        sl = find_flow_report(report_group_slug, stop)
    except FlowReport.DoesNotExist:
        return ""

    exclude = [u'Backlog', u'Done', ]
    wip = 0
    for state, count in sl.state_counts.items():
        if state not in exclude:
            wip += count

    return wip


def find_cycle_time_ave(report_group_slug, stop):
    try:
        dr = DailyRecord.objects.get(
            date=make_end_date(date=stop),
            group=report_group_slug,
        )
    except DailyRecord.DoesNotExist:
        print "No Daily Record: %s %s" % (report_group_slug, make_end_date(date=stop))
        raise

    return dr.moving_cycle_time


def moving_data(report_group_slug, start, stop):
    query = Kard.objects.filter(
        done_date__gte=start,
        done_date__lte=stop,)

    kards = list(ReportGroup(report_group_slug, query).queryset)

    bad_kards = [k for k in kards if k.cycle_time is None]
    print "Bad cards"
    print "*" * 10
    print [k.key for k in bad_kards]

    features = [k for k in kards if k.is_card]
    defects = [k for k in kards if not k.is_card]
    over_sla = [k for k in kards if k.cycle_time > k.service_class['upper']]
    card_cycle_ave = average([k.cycle_time for k in kards]) or 0
    card_stddev = standard_deviation([k.cycle_time for k in kards]) or 0

    wip = find_wip(report_group_slug, stop)
    tpa = daily_throughput_average(report_group_slug, stop)

    try:
        little_law = int(round(wip / float(tpa)))
    except:
        little_law = ""

    cycle_time_ave = find_cycle_time_ave(report_group_slug, stop)

    data = {
        'start': start,
        'stop': stop,
        'features': len(features),
        'bugfixes': len(defects),
        'little_law': little_law,
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
    print "Cyc: %s" % data['cycle_average']
    print "Std: %s" % data['stddev']


def weekly_moving_data(report_group_slug, start):
    start = parse_date(start)
    stop = start + relativedelta(days=6)

    start = make_start_date(date=start)
    stop = make_end_date(date=stop)
    return moving_data(report_group_slug, start, stop)


if __name__ == "__main__":
    import sys
    try:
        data = weekly_moving_data(sys.argv[2], sys.argv[1])
    except IndexError:
        print "{week_start_date} {report_group_slug}"
        raise
    print_data(data)
