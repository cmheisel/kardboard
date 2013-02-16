from datetime import datetime

from kardboard.models import Kard, ReportGroup
from kardboard.util import standard_deviation, make_start_date, make_end_date, average


def year_std_dev(year):
    year_start = make_start_date(date=datetime(year, 1, 1))
    year_end = make_end_date(date=datetime(year, 12, 31))

    rg = ReportGroup('dev', Kard.objects.filter(start_date__gte=year_start, done_date__lte=year_end))

    cards = [c for c in rg.queryset if c.is_card]
    cycle_times = [c.cycle_time for c in cards]

    data = {}
    data['n'] = len(cards)
    data['ave'] = average(cycle_times)
    data['std'] = standard_deviation(cycle_times)
    return data


if __name__ == "__main__":
    import sys
    print year_std_dev(int(sys.argv[1]))
