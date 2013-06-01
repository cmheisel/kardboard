from kardboard.models.kard import Kard
from kardboard.models.statelog import StateLog

class Funnel(object):
    def __init__(self, state, config):
        self.config = config
        self.state = state

    @property
    def throughput(self):
        return self.config.get('throughput', None)

    def find_cards(self):
        cards = Kard.objects.filter(
            state=self.state,
        ).exclude('_ticket_system_data')
        return list(cards)

    def state_duration(self, card):
        statelog = StateLog.objects.filter(card=card, state=self.state).order_by('-entered')
        return statelog[0].duration

    def times_in_state(self):
        times_in_state = {}
        for c in self.find_cards():
            times_in_state[c.key] = self.state_duration(c)
        return times_in_state

    def ordered_cards(self):
        cards = self.find_cards()

        cards_with_ordering = [c for c in cards if c.priority]
        cards_without_ordering = [c for c in cards if c.priority is None]

        cards_with_ordering = sorted(cards_with_ordering, key=lambda c: c.priority)
        cards_without_ordering = sorted(cards_without_ordering, key=lambda c: self.state_duration(c))
        cards_without_ordering.reverse()
        cards = cards_with_ordering + cards_without_ordering
        return cards
