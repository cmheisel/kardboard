"""
Utilities for getting WIP limit data about a team
"""


class WIPLimits(object):
    """
    Stores data about a team's wip limit rules
    """
    def __init__(self, columns=None, conwip=None):
        if columns is None:
            columns = {}
        self._conwip = conwip
        self._columns = columns
        self._limits = self._calculate_limits()

    def _calculate_limits(self):
        _limits = {}
        for key, value in self._columns.items():
            _limits[key] = value
        _limits['conwip'] = self._conwip
        return _limits

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        return self._limits[key]
