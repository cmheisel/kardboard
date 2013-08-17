from collections import defaultdict


def wip_state(wip, wip_limit):
    if wip_limit is None:
        return "at"
    if wip > wip_limit:
        return "over"
    if wip < wip_limit:
        return "under"
    return "at"


class TeamBoard(object):
    """
    TeamBoard's take in states, optionally WIP limits, and optionally
    cards.

    It provides methods for assembling that data into a kanban board
    """

    def __init__(self, name, states, wip_limits=None):
        self.name = name
        self.states = states
        self.cards_by_state = defaultdict(list)

        if wip_limits is None:
            wip_limits = {}
        self.wip_limits = wip_limits

    def add_cards(self, cards):
        for c in cards:
            self.cards_by_state[c.state].append(c)

    @property
    def columns(self):
        columns = []
        for state in self.states.active:
            wip_limit = self.wip_limits.get(state.name, None)
            wip = len(self.cards_by_state[state.name])
            if state.buffer:
                wip += len(self.cards_by_state[state.buffer])

            columns.append({
                'name': state.name,
                'buffer': state.buffer,
                'wip_limit': wip_limit,
                'wip': wip,
                'wip_state': wip_state(wip, wip_limit),
                'cards': self.cards_by_state[state.name],
                'buffer_cards': self.cards_by_state[state.buffer],
            })
        return columns
