"""
Tests for services/wiplimits
"""

import unittest2


class WIPLimitTests(unittest2.TestCase):
    """
    Tests for WIPLimit helper class
    """
    def _get_target_class(self):
        from kardboard.services.wiplimits import WIPLimits
        return WIPLimits

    def test_conwip(self):
        """
        If you pass in an explict conwip, you should get it back
        """
        w = self._get_target_class()(
            conwip=5
        )
        assert w['conwip'] == 5

    def test_conwip_default_to_none(self):
        """
        If you don't pass in a conwip or anything else,
        the team defaults to no wip limits
        """
        w = self._get_target_class()()
        assert w['conwip'] is None
