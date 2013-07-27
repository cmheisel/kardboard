"""
Classes that provide reports on card data.
"""
from collections import namedtuple, defaultdict

HistogramRow = namedtuple(
    'HistogramRow',
    ['days', 'count', 'percent']
)


class CycleTimeDistribution(object):
    def __init__(self, cards):
        self.cards = cards
        object.__init__(self)

    def histogram(self):
        total = len(self.cards)
        d = defaultdict(int)
        for c in self.cards:
            d[c.cycle_time] += 1

        days = d.keys()
        days.sort()
        rows = []
        for day in days:
            cumulative = sum([r.count for r in rows])
            cumulative += d[day]
            row = HistogramRow(
                days=day,
                count=d[day],
                percent=cumulative / float(total)
            )
            rows.append(row)
        return rows
