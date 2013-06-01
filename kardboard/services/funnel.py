import datetime

from dateutil import relativedelta

from kardboard.models.kard import Kard
from kardboard.models.statelog import StateLog

class Funnel(object):
    def __init__(self, state, config):
        self.config = config
        self.state = state

    @property
    def throughput(self):
        return self.config.get('throughput', None)

    def is_authorized(self, username):
        user_list = self.config.get('auth', [])
        if len(user_list) is 0:
            return True
        if username in user_list:
            return True
        return False

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

    def markers(self):
        funnel_markers = []
        if self.throughput:
            counter = 0
            batch_counter = 0
            for k in self.find_cards():
                if counter % self.throughput == 0:
                    if len(funnel_markers) > 0:
                        base_date = funnel_markers[-1]
                    else:
                        base_date = datetime.datetime.now()
                    est_done_date = base_date + relativedelta.relativedelta(days=1)
                    if est_done_date.weekday() == 5:  # Saturday
                        est_done_date = est_done_date + relativedelta.relativedelta(days=2)
                    if est_done_date.weekday() == 6:  # Sunday
                        est_done_date = est_done_date + relativedelta.relativedelta(days=1)
                    funnel_markers.append(est_done_date)
                    batch_counter += 1
                counter +=1
        return funnel_markers
