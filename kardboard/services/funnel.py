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
