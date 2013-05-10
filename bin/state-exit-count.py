import datetime
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from kardboard.util import make_start_date, make_end_date, average, median
from kardboard.models.statelog import StateLog


def histogram(counts):
    d = defaultdict(int)
    for c in counts:
        d[c] += 1
    return dict(d)


def exit_counts(state, months, raw=False):
    end = make_end_date(date=datetime.datetime.now())

    start = end - relativedelta(months=months)
    start = make_start_date(date=start)

    counts = []
    data = []

    current_date = start
    while current_date <= end:
        if current_date.weekday() == 5:  # Saturday
            current_date += relativedelta(days=2)
        elif current_date.weekday() == 6:  # Sunday
            current_date += relativedelta(days=1)

        range_start = make_start_date(date=current_date)
        range_end = make_end_date(date=current_date)

        otis_exit_count = StateLog.objects.filter(
            state=state,
            exited__gte=range_start,
            exited__lte=range_end,
        ).count()

        data.append((current_date, otis_exit_count))
        counts.append(otis_exit_count)
        current_date = current_date + relativedelta(days=1)

    counts.sort()

    print "%s -- %s" % (start, end)
    print "Median: %s" % median(counts)
    print "Average: %s" % average(counts)
    print "Min: %s" % counts[0]
    print "Max: %s" % counts[-1]

    hist = histogram(counts)
    keys = hist.keys()
    keys.sort()
    for k in keys:
        print "%s\t%s" % (k, hist[k])

    if raw is True:
        for date, count in data:
            print "%s\t%s" % (date, count)


if __name__ == "__main__":
    import sys
    exit_counts(sys.argv[1], int(sys.argv[2]))
