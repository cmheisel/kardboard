from kardboard.models import Kard, ReportGroup
from kardboard.util import standard_deviation, make_start_date, make_end_date, average

def parse_date(datestr):
    from dateutil import parser
    return parser.parse(datestr)

def std_dev(start, stop):
    start = make_start_date(date=start)
    stop = make_end_date(date=stop)

    rg = ReportGroup('dev', Kard.objects.filter(start_date__gte=start, done_date__lte=stop))

    cards = [c for c in rg.queryset if c.is_card]
    cycle_times = [c.cycle_time for c in cards]

    print "%s -- %s" % (start, stop)
    print "\t Sample: %s" % len(cards)
    print "\t Ave: %s" % average(cycle_times)
    print "\t Stdev: %s" % standard_deviation(cycle_times)

    cards_by_class = {}
    for c in cards:
        cards_by_class.setdefault(c.service_class['name'], [])
        cards_by_class[c.service_class['name']].append(c)

    for sclass, cards in cards_by_class.items():
        cycle_times = [c.cycle_time for c in cards]

        print "\t ## %s" % (sclass)
        print "\t\t Sample: %s" % len(cards)
        print "\t\t Ave: %s" % average(cycle_times)
        print "\t\t Stdev: %s" % standard_deviation(cycle_times)


if __name__ == "__main__":
    import sys
    start = parse_date(sys.argv[1])
    stop= parse_date(sys.argv[2])
    print std_dev(start, stop)
