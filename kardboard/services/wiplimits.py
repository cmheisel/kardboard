"""
Utilities for getting WIP limit data about a team
"""


class WIPLimits(object):
    """
    Stores data about a team's wip limit rules
    """
    def __init__(self, conwip=None):
        self.conwip = conwip
