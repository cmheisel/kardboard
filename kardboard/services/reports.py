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

    def days(self):
        days = list(set([c.cycle_time for c in self.cards]))
        days.sort()
        return days

    def service_classes(self):
        sclasses = list(set([c.service_class['name'] for c in self.cards]))
        sclasses.sort()
        return sclasses

    def _cards_by_service_class(self):
        cards = {}
        for c in self.cards:
            sclass_cards = cards.get(c.service_class['name'], [])
            sclass_cards.append(c)
            cards[c.service_class['name']] = sclass_cards
        return cards

    def service_class_series(self):
        days = self.days()

        series = {}
        for sclass, cards in self._cards_by_service_class().items():
            seri = defaultdict(int)
            for day in days:
                seri[day] = 0
            for c in cards:
                seri[c.cycle_time] += 1

            keys = seri.keys()
            keys.sort()
            values = []
            for k in keys:
                values.append(seri[k])
            series[sclass] = values
        return series
