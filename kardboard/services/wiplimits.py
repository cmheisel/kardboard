"""
Utilities for getting WIP limit data about a team
"""


class WIPLimits(object):
    """
    Stores data about a team's wip limit rules
    """
    def __init__(self, columns=None, conwip=None, name=None):
        if columns is None:
            columns = {}
        self.name = name
        self._conwip = conwip
        self._columns = columns
        self._limits = self._calculate_limits()

    def _calculate_limits(self):
        _limits = {}
        for key, value in self._columns.items():
            _limits[key] = value

        if self._columns.values() and self._conwip is None:
            _limits['conwip'] = sum(self._columns.values())
        else:
            _limits['conwip'] = self._conwip
        return _limits

    def get(self, key, default=None):
        return self._limits.get(key, default)

    def __getitem__(self, key):
        return self._limits[key]
