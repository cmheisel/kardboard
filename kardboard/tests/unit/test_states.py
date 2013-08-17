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


class BufferStatesTests(unittest2.TestCase):
    def setUp(self):
        CARD_STATES = [
            'Backlog',
            ('Elaborating', 'Ready: Building'),
            ('Building', 'Ready: Testing',),
            ('Testing', 'Build to OTIS',),
            ('OTIS Verify', 'Prodward Bound',),
            'Done',
        ]

        BACKLOG_STATE = 0
        START_STATE = 3
        DONE_STATE = -1

        self.config = {
            'CARD_STATES': CARD_STATES,
            'BACKLOG_STATE': BACKLOG_STATE,
            'START_STATE': START_STATE,
            'DONE_STATE': DONE_STATE,
        }

        self.states = self._make_one()

    def _get_target_class(self):
        from kardboard.models import States
        return States

    def _make_one(self, *args, **kwargs):
        if 'config' not in kwargs.keys():
            kwargs['config'] = self.config
        return self._get_target_class()(*args, **kwargs)

    def test_find_start(self):
        assert "Building" == self.states.start

    def test_find_backlog(self):
        assert "Backlog" == self.states.backlog

    def test_find_done(self):
        assert "Done" == self.states.done

    def test_pre_start(self):
        expected = ['Backlog', 'Elaborating', 'Ready: Building']
        assert expected == self.states.pre_start

    def test_in_progress(self):
        expected = [
            'Elaborating',
            'Ready: Building',
            'Building',
            'Ready: Testing',
            'Testing',
            'Build to OTIS',
            'OTIS Verify',
            'Prodward Bound',
        ]
        assert expected == self.states.in_progress

    def test_iteration(self):
        expected = [
            'Backlog',
            'Elaborating',
            'Ready: Building',
            'Building',
            'Ready: Testing',
            'Testing',
            'Build to OTIS',
            'OTIS Verify',
            'Prodward Bound',
            'Done',
        ]
        assert expected == [state for state in self.states]

    def test_str(self):
        expected = [
            'Backlog',
            'Elaborating',
            'Ready: Building',
            'Building',
            'Ready: Testing',
            'Testing',
            'Build to OTIS',
            'OTIS Verify',
            'Prodward Bound',
            'Done',
        ]
        expected = str(expected)
        assert expected == str(self.states)

    def test_by_index(self):
        assert "Backlog" == self.states[0]
        assert "Done" == self.states[-1]
        assert "Ready: Building" == self.states[2]

    def test_find_by_slug(self):
        expected = "Build to OTIS"
        assert expected == self.states.find_by_slug('build-to-otis')

    def test_orderable(self):
        expected = ['Backlog']
        assert expected == self.states.orderable

    def test_index(self):
        assert 0 == self.states.index("Backlog")

    def test_for_forms(self):
        expected = (
            ('', ''),
            ('Backlog', 'Backlog'),
            ('Elaborating', 'Elaborating'),
            ('Ready: Building', 'Ready: Building'),
            ('Building', 'Building'),
            ('Ready: Testing', 'Ready: Testing'),
            ('Testing', 'Testing'),
            ('Build to OTIS', 'Build to OTIS'),
            ('OTIS Verify', 'OTIS Verify'),
            ('Prodward Bound', 'Prodward Bound'),
            ('Done', 'Done'),
        )
        assert expected == self.states.for_forms

    def test_active_states(self):
        assert 6 == len(self.states.active)
