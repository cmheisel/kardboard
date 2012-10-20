from kardboard.app import app


class PersonCardSet(object):
    def __init__(self, name):
        super(PersonCardSet, self).__init__()
        self.name = name
        self.cards = set()
        self.defects = set()

    @property
    def all_cards(self):
        return self.cards.union(self.defects)

    def add_card(self, card):
        defect_types = app.config.get('DEFECT_TYPES', ())
        if card.type in defect_types:
            self.defects.add(card)
        else:
            self.cards.add(card)

    @property
    def count(self):
        return len(self.cards)

    @property
    def sorted_cards(self):
        cards = list(self.cards)
        cards.sort(key=lambda c: c.done_date, reverse=True)
        return cards

    @property
    def sorted_defects(self):
        defects = list(self.defects)
        defects.sort(key=lambda c: c.done_date, reverse=True)
        return defects

    @property
    def cycle_time(self):
        times = [c.cycle_time for c in self.all_cards]
        return int(round(float(sum(times)) / len(times)))

    def __cmp__(self, other):
        return cmp(self.count, other.count)
