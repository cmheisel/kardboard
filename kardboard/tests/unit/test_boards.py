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

        if 'current_cycle_time' in kwargs.keys():
            mock_card.current_cycle_time.return_value = \
                kwargs['current_cycle_time']
            del kwargs['current_cycle_time']

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

    def test_placeholders_with_no_wip(self):
        bd = self._make_one()

        cards = []
        for i in xrange(2):
            title = "Ready Card %s" % i
            state = "Ready: Building"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert len(col['placeholders']) == 0

    def test_placeholders_with_wip(self):
        self.mock_wip_limits = {
            'Elaboration': 4,
        }
        bd = self._make_one()

        cards = []
        for i in xrange(2):
            title = "Ready Card %s" % i
            state = "Ready: Building"
            cards.append(self._make_card(title=title, state=state))

        bd.add_cards(cards)
        col = bd.columns[1]

        assert len(col['placeholders']) == 2

    def test_card_column_sorts_wip_cards(self):
        bd = self._make_one()

        cards = []
        for i in xrange(1, 5):  # Returns 4 cards
            title = "Building %s" % i
            state = "Building"
            current_cycle_time = i
            cards.append(self._make_card(
                title=title,
                state=state,
                current_cycle_time=current_cycle_time
            ))

        cards = [cards[2], cards[0], cards[3], cards[1]]

        bd.add_cards(cards)
        col = bd.columns[2]

        expected = [
            "Building 4",
            "Building 3",
            "Building 2",
            "Building 1",
        ]
        actual = [c.title for c in col['cards']]
        assert expected == actual

    def test_card_buffer_sorts_wip_cards(self):
        bd = self._make_one()

        cards = []
        for i in xrange(1, 5):  # Returns 4 cards
            title = "Ready: Testing %s" % i
            state = "Ready: Testing"
            current_cycle_time = i
            cards.append(self._make_card(
                title=title,
                state=state,
                current_cycle_time=current_cycle_time
            ))

        cards = [cards[2], cards[0], cards[3], cards[1]]

        bd.add_cards(cards)
        col = bd.columns[2]

        expected = [
            "Ready: Testing 4",
            "Ready: Testing 3",
            "Ready: Testing 2",
            "Ready: Testing 1",
        ]
        actual = [c.title for c in col['buffer_cards']]
        assert expected == actual
