"""
Tests for services/boards
"""

import unittest2
import mock


class TeamBoardTests(unittest2.TestCase):
    def setUp(self):
        from kardboard.models.states import States, State

        self.State = State
        self.mock_states = States()
        self.mock_states.states = [
            State("Backlog", None, False),
            State("Elaboration", "Ready: Building", False),
            State("Ready: Building", None, True),
            State("Building", "Ready: Testing", False),
            State("Ready: Testing", None, True),
            State("Testing", "Build to OTIS", False),
            State("Build to OTIS", None, True),
            State("OTIS Verify", "Prodward Bound", False),
            State("Proward Bound", None, True),
            State("Done", None, False),
        ]
        self.mock_wip_limits = {}

    def _get_target_class(self):
        from kardboard.services.boards import TeamBoard
        return TeamBoard

    def _make_one(self, *args, **kwargs):
        kwargs.setdefault('states', self.mock_states)
        kwargs.setdefault('name', "Team Name Here")
        kwargs.setdefault('wip_limits', self.mock_wip_limits)
        return self._get_target_class()(*args, **kwargs)

    def _make_card(self, **kwargs):
        mock_card = mock.Mock()
        for key, value in kwargs.items():
            setattr(mock_card, key, value)
        return mock_card

    def test_name(self):
        b = self._get_target_class()(
            name="Test Team",
            states=self.mock_states,
        )
        assert b.name == "Test Team"

    def test_columns_without_buffers(self):
        self.mock_states.states = [
            self.State("Backlog", None, False),
            self.State("Elaboration", None, False),
            self.State("Ready for Building", None, False),
            self.State("Building", None, False),
            self.State("Testing", None, False),
            self.State("Done", None, False),
        ]
        bd = self._make_one(states=self.mock_states)
        assert len(bd.columns) == 6

    def test_columns_with_buffers(self):
        bd = self._make_one()
        assert len(bd.columns) == 6

    def test_columns_return_column_name(self):
        bd = self._make_one()
        col = bd.columns[1]

        assert col['name'] == "Elaboration"

    def test_columns_return_column_buffer(self):
        bd = self._make_one()
        col = bd.columns[1]

        assert col['buffer'] == "Ready: Building"

    def test_columns_return_no_column_buffer(self):
        self.mock_states.states = [
            self.State("Backlog", None, False),
            self.State("Elaboration", None, False),
            self.State("Ready for Building", None, False),
            self.State("Building", None, False),
            self.State("Testing", None, False),
            self.State("Done", None, False),
        ]
        bd = self._make_one(states=self.mock_states)
        col = bd.columns[2]

        assert col['buffer'] is None

    def test_columns_return_wip_limit(self):
        self.mock_wip_limits = {
            'Elaboration': 2,
        }
        bd = self._make_one()
        col = bd.columns[1]

        assert col['wip_limit'] == 2

    def test_columns_return_wip_info_with_cards(self):
        self.mock_wip_limits = {
            'Elaboration': 2,
        }
        bd = self._make_one()

        cards = []
        for i in xrange(3):
            title = "Elabo Card %s" % i
            state = "Elaboration"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert col['wip'] == 3

    def test_columns_return_wip_state_over(self):
        self.mock_wip_limits = {
            'Elaboration': 2,
        }
        bd = self._make_one()

        cards = []
        for i in xrange(3):
            title = "Elabo Card %s" % i
            state = "Elaboration"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert col['wip_state'] == "over"

    def test_columns_return_wip_state_under(self):
        self.mock_wip_limits = {
            'Elaboration': 2,
        }
        bd = self._make_one()

        cards = []
        for i in xrange(1):
            title = "Elabo Card %s" % i
            state = "Elaboration"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert col['wip_state'] == "under"

    def test_columns_return_wip_state_at(self):
        self.mock_wip_limits = {
            'Elaboration': 2,
        }
        bd = self._make_one()

        cards = []
        for i in xrange(2):
            title = "Elabo Card %s" % i
            state = "Elaboration"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert col['wip_state'] == "at"

    def test_wip_count_includes_buffers(self):
        self.mock_wip_limits = {
            'Elaboration': 2,
        }
        bd = self._make_one()

        cards = []
        for i in xrange(2):
            title = "Elabo Card %s" % i
            state = "Elaboration"
            cards.append(self._make_card(title=title, state=state))
            title = "Ready Card %s" % i
            state = "Ready: Building"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert col['wip'] == 4

    def test_card_column_returns_cards(self):
        bd = self._make_one()

        cards = []
        for i in xrange(2):
            title = "Elabo Card %s" % i
            state = "Elaboration"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert len(col['cards']) == 2

    def test_card_column_returns_buffered_cards(self):
        bd = self._make_one()

        cards = []
        for i in xrange(2):
            title = "Ready Card %s" % i
            state = "Ready: Building"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert len(col['buffer_cards']) == 2
