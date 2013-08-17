

class TeamBoard(object):
    """
    TeamBoard's take in states, optionally WIP limits, and optionally
    cards.

    It provides methods for assembling that data into a kanban board
    """

    def __init__(self, name, states, wip_limits=None):
        self.name = name
        self.states = states

        if wip_limits is None:
            wip_limits = {}
        self.wip_limits = wip_limits

    @property
    def columns(self):
        columns = []
        for state in self.states.active:
            columns.append({
                'name': state.name,
                'buffer': state.buffer,
                'wip_limit': self.wip_limits.get(state.name, None)
            })
        return columns
