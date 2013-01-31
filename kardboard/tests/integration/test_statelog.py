import mock

from datetime import datetime
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


class StatelogKardTests(StatelogTests):
    def setUp(self):
        super(StatelogKardTests, self).setUp()

    def tearDown(self):
        self._get_target_class().objects.all().delete()

    def test_existing_kard_state_change(self):
        card = self.cards[0]
        self.assert_(card.id)
        card.state = self.states[1]
        card.save()

        StateLog = self._get_target_class()
        sl = StateLog.objects.get(card=card, state=self.states[1])
        self.assertEqual(0, sl.duration)

    def test_new_kard_state_log(self):
        card = self.make_card(state=self.states[0])
        self.assertEqual(None, card.id)

        card.save()
        StateLog = self._get_target_class()
        sl = StateLog.objects.get(card=card, state=card.state)
        self.assertEqual(0, sl.duration)

    @mock.patch('kardboard.models.statelog.now')
    def test_full_state_life_cycle(self, mocked_now):
        StateLog = self._get_target_class()

        # Created a new card 10 days ago in Todo
        mocked_now.return_value = datetime.now() - relativedelta(days=10)
        card = self.make_card(state=self.states[0])
        print "CARD UNDER TEST IS %s" % card.key
        self.assertEqual(None, card.id)
        card.save()
        sln = StateLog.objects.get(card=card, state=self.states[0])
        self.assertEqualDateTimes(sln.entered, mocked_now.return_value)

        # Moved that card 8 days ago into Doing
        mocked_now.return_value = datetime.now() - relativedelta(days=8)
        card.state = self.states[1]
        card.save()
        slo = StateLog.objects.get(card=card, state=self.states[0])
        self.assertEqualDateTimes(slo.exited, mocked_now.return_value)
        self.assertEqual(48, slo.duration)

        sln = StateLog.objects.get(card=card, state=self.states[1])
        self.assertEqualDateTimes(sln.entered, mocked_now.return_value)
        self.assertEqual(0, sln.duration)

        # Moved that card 1 day ago into Done
        mocked_now.return_value = datetime.now() - relativedelta(days=1)
        card.state = self.states[2]
        card.save()
        print StateLog.objects.filter(card=card).order_by('created_at')
        slo = StateLog.objects.get(card=card, state=self.states[1])
        self.assertEqualDateTimes(slo.exited, mocked_now.return_value)
        self.assertEqual(7 * 24, slo.duration)

        sln = StateLog.objects.get(card=card, state=self.states[2])
        self.assertEqualDateTimes(sln.entered, mocked_now.return_value)
        self.assertEqual(0, sln.duration)
