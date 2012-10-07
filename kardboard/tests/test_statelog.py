from dateutil.relativedelta import relativedelta

from kardboard.tests.core import KardboardTestCase


class StatelogTests(KardboardTestCase):
    def setUp(self):
        super(StatelogTests, self).setUp()
        from kardboard.models.states import States
        self.states = States()
        self.cards = [self.make_card() for i in xrange(0, 5)]
        [card.save() for card in self.cards]

        entered = self.now() - relativedelta(days=2)
        state = self.states[0]
        sl = self._make_one(
            entered=entered,
            state=state,
        )
        self.sl = sl

    def _get_target_class(self):
        from kardboard.models.statelog import StateLog
        return StateLog

    def _make_one(self, *args, **kwargs):
        defaults = {
            'entered': self.now(),
            'card': self.cards[0],
            'state': self.states[0],
        }
        defaults.update(kwargs)
        return super(StatelogTests, self)._make_one(*args, **defaults)

    def test_make_one(self):
        sl = self._make_one()
        sl.save()
        assert sl.id

    def test_state_duration_calc(self):
        expected = 48
        self.assertEqual(expected, self.sl.duration)

    def test_state_duration_non_storage(self):
        expected = None
        self.assertEqual(expected, self.sl._duration)

    def test_state_duration_storage(self):
        self.sl.exited = self.now()
        self.sl.save()
        expected = 48
        self.assertEqual(expected, self.sl._duration)
