

class TeamBoard(object):
    """
    TeamBoard's take in states, optionally WIP limits, and optionally
    cards.

    It provides methods for assembling that data into a kanban board
    """

    def __init__(self, name, states, wip_limits=None):
        self.name = name
        self.states = states
        self.cards_by_state = {}
        for state_name in self.states:
            self.cards_by_state.setdefault(state_name, [])

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
            columns.append({
                'name': state.name,
                'buffer': state.buffer,
                'wip_limit': self.wip_limits.get(state.name, None),
                'wip': len(self.cards_by_state[state.name]),
            })
        return columns
