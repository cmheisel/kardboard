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

    def test_column_limit(self):
        """
        If you pass in a column limit it should return it.
        """
        w = self._get_target_class()(
            columns={'Todo': 5}
        )
        assert w['Todo'] == 5

    def test_multiple_columns(self):
        """
        If you pass in multiple columns, you should
        get them back
        """
        w = self._get_target_class()(
            columns={
                'Todo': 5,
                'Doing': 15,
            }
        )
        assert w['Todo'] == 5
        assert w['Doing'] == 15

    def test_get_method_key_exists(self):
        """
        A WIPlimit object should exhibit
        dictionary-like get behavior
        """
        w = self._get_target_class()(
            columns={
                'Todo': 5,
            }
        )
        assert w.get('Todo', None) == 5

    def test_get_method_key_doesnt_exist(self):
        """
        A WIPlimit object should exhibit
        dictionary-like get behavior
        """
        w = self._get_target_class()(
            columns={
                'Todo': 5,
            }
        )
        assert w.get('Doing', 1) == 1

    def test_conwip_calculated_if_not_passed_one_col(self):
        """
        If given one or more columns and no conwip
        then WIPLimits returns the sum of all known columns
        """
        w = self._get_target_class()(
            columns={
                'Todo': 5,
            }
        )
        assert w['conwip'] == 5

    def test_conwip_calculated_if_not_passed_two_col(self):
        """
        If given one or more columns and no conwip
        then WIPLimits returns the sum of all known columns
        """
        w = self._get_target_class()(
            columns={
                'Todo': 5,
                'Doing': 10
            }
        )
        assert w['conwip'] == 15

    def test_conwip_honored_if_passed(self):
        """
        If a conwip is explicitly passed, and columns are passed,
        then the explicit conwip is honored regardless of math.
        """
        w = self._get_target_class()(
            columns={
                'Todo': 5,
                'Doing': 10
            },
            conwip=5,
        )
        assert w['conwip'] == 5
