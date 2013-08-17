

class TeamBoard(object):
    """
    TeamBoard's take in states, optionally WIP limits, and optionally
    cards.

    It provides methods for assembling that data into a kanban board
    """

    def __init__(self, name, states):
        self.name = name
        self.states = states

    @property
    def columns(self):
        columns = []
        for state in self.states.active:
            columns.append({
                'name': state.name,
                'buffer': state.buffer,
            })
        return columns
