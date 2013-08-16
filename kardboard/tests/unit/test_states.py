"""
Tests for models/states
"""

import unittest2


class StatesTests(unittest2.TestCase):
    def setUp(self):
        super(StatesTests, self).setUp()
        self.config = {}
        self.config['CARD_STATES'] = (
            'Backlog',
            'In Progress',
            'Deploy',
            'Done',
        )

    def _get_target_class(self):
        from kardboard.models import States
        return States

    def _make_one(self, *args, **kwargs):
        if 'config' not in kwargs.keys():
            kwargs['config'] = self.config
        return self._get_target_class()(*args, **kwargs)

    def test_orderable(self):
        states = self._make_one()
        expected = ['Backlog']
        actual = states.orderable
        assert expected == actual

    def test_find_by_slug(self):
        states = self._make_one()
        expected = 'Deploy'
        actual = states.find_by_slug('deploy')
        assert expected == actual

    def test_iteration(self):
        states = self._make_one()
        expected = [state for state in self.config['CARD_STATES']]
        actual = [state for state in states]
        self.assertEqual(expected, actual)

    def test_default_state_groups(self):
        states = self._make_one()
        expected = 'Backlog'
        self.assertEqual(expected, states.backlog)
        self.assertEqual([expected, ], states.pre_start)

        expected = 'In Progress'
        self.assertEqual(expected, states.start)

        expected = ['In Progress', 'Deploy']
        self.assertEqual(expected, states.in_progress)

        expected = 'Done'
        self.assertEqual(expected, states.done)

    def test_configured_state_groups(self):
        self.config['CARD_STATES'] = (
            'Backlog',
            'Planning',
            'In Progress',
            'Testing',
            'Deploy',
            'Done',
            'Archive',
        )
        self.config['BACKLOG_STATE'] = 0
        self.config['START_STATE'] = 2
        self.config['DONE_STATE'] = -2

        states = self._make_one()

        expected = ['Backlog', 'Planning']
        self.assertEqual(expected[0], states.backlog)
        self.assertEqual(expected, states.pre_start)

        expected = 'In Progress'
        self.assertEqual(expected, states.start)

        expected = ['Planning', 'In Progress', 'Testing', 'Deploy']
        self.assertEqual(expected, states.in_progress)

        expected = 'Done'
        self.assertEqual(expected, states.done)

    def test_for_forms(self):
        states = self._make_one()

        expected = (
            ('', ''),
            ('Backlog', 'Backlog'),
            ('In Progress', 'In Progress'),
            ('Deploy', 'Deploy'),
            ('Done', 'Done'),
        )
        self.assertEqual(expected, states.for_forms)
