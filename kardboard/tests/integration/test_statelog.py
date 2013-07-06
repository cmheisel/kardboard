import mock
import pytest

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
        self.config['SERVICE_CLASSES'] = {
            'Speedy': {'lower': 2, 'upper': 4, 'wip': .05, 'name': 'Speedy'},
            'default': {'lower': 5, 'upper': 15, 'name': 'default'},
        }

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

    @pytest.mark.questionable
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
        slo = StateLog.objects.get(card=card, state=self.states[1])
        self.assertEqualDateTimes(slo.exited, mocked_now.return_value)
        self.assertEqual(7 * 24, slo.duration)

        sln = StateLog.objects.get(card=card, state=self.states[2])
        self.assertEqualDateTimes(sln.entered, mocked_now.return_value)
        self.assertEqual(0, sln.duration)

    @mock.patch('kardboard.models.statelog.now')
    def test_service_class_changes_sets_exited_at(self, mocked_now):
        StateLog = self._get_target_class()

        # Created a new card 10 days ago in Todo
        original_entered = datetime.now() - relativedelta(days=10)
        mocked_now.return_value = original_entered
        card = self.make_card(state=self.states[0], _service_class="default")
        self.assertEqual(None, card.id)
        card.save()
        sln = StateLog.objects.get(card=card, state=self.states[0])
        self.assertEqualDateTimes(sln.entered, mocked_now.return_value)

        # Upgraded that card's service class 8 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=8)
        card._service_class = "Speedy"
        card.save()
        card.ticket_system.actually_update()
        slo = StateLog.objects.get(card=card)
        self.assertEqualDateTimes(slo.entered, original_entered)

    def assertEnteredStateOnceAt(self, card, state, when):
        StateLog = self._get_target_class()
        sln = StateLog.objects.get(card=card, state=state)
        self.assertEqualDateTimes(sln.entered, when)
        assert sln.exited is None

    def assertExitedStateOnceAt(self, card, state, when):
        StateLog = self._get_target_class()
        sln = StateLog.objects.get(card=card, state=state)
        self.assertEqualDateTimes(sln.exited, when)

    def assertEnteredStateNTimesRecently(self, times, card, state, when):
        StateLog = self._get_target_class()
        state_logs = StateLog.objects.filter(card=card, state=state).order_by('-entered')
        assert times == len(state_logs)
        self.assertEqualDateTimes(state_logs[0].entered, when)
        assert state_logs[0].exited is None

        for i in xrange(1, times-1):
            assert state_logs[i].entered != when
            assert state_logs[i].exited != when

    def assertExitedStateNTimesRecently(self, times, card, state, when):
        StateLog = self._get_target_class()
        state_logs = StateLog.objects.filter(card=card, state=state).order_by('-entered')
        assert times == len(state_logs)
        self.assertEqualDateTimes(state_logs[0].exited, when)
        assert state_logs[0].entered is not None

        for i in xrange(1, times-1):
            assert state_logs[i].entered != when
            assert state_logs[i].exited != when

    @mock.patch('kardboard.models.statelog.now')
    def test_card_going_back_and_forth(self, mocked_now):
        TODO = 'Todo'
        PLANNING = 'Planning'
        DOING = 'Doing'
        TESTING = 'Testing'
        DEPLOYING = 'Deploying'
        DONE = 'Done'

        # Created a new card 30 days ago in Todo
        mocked_now.return_value = datetime.now() - relativedelta(days=30)
        card = self.make_card(state=TODO)
        card.save()

        self.assertEnteredStateOnceAt(card, TODO, mocked_now.return_value)

        # Now move it to Planning 29 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=29)
        card.state = PLANNING
        card.save()
        self.assertExitedStateOnceAt(card, TODO, mocked_now.return_value)
        self.assertEnteredStateOnceAt(card, PLANNING, mocked_now.return_value)

        # Now move it back to TODO 25 days agao
        mocked_now.return_value = datetime.now() - relativedelta(days=25)
        card.state = TODO
        card.save()

        self.assertExitedStateOnceAt(card, PLANNING, mocked_now.return_value)
        self.assertEnteredStateNTimesRecently(2, card, TODO, mocked_now.return_value)

        # Now move it back to PLANNING 24 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=24)
        card.state = PLANNING
        card.save()

        self.assertExitedStateNTimesRecently(2, card, TODO, mocked_now.return_value)
        self.assertEnteredStateNTimesRecently(2, card, PLANNING, mocked_now.return_value)

        # Now move it to DOING 24 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=24)
        card.state = DOING
        card.save()

        self.assertExitedStateNTimesRecently(2, card, PLANNING, mocked_now.return_value)
        self.assertEnteredStateOnceAt(card, DOING, mocked_now.return_value)

        # Now move it to TESTING 22 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=22)
        card.state = TESTING
        card.save()

        self.assertExitedStateOnceAt(card, DOING, mocked_now.return_value)
        self.assertEnteredStateOnceAt(card, TESTING, mocked_now.return_value)

        # Now move it back to DOING 22 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=20)
        card.state = DOING
        card.save()

        self.assertExitedStateOnceAt(card, TESTING, mocked_now.return_value)
        self.assertEnteredStateNTimesRecently(2, card, DOING, mocked_now.return_value)

        # Now move it to TESTING 19 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=19)
        card.state = TESTING
        card.save()

        self.assertExitedStateNTimesRecently(2, card, DOING, mocked_now.return_value)
        self.assertEnteredStateNTimesRecently(2, card, TESTING, mocked_now.return_value)

        # Now move it back to DOING again again 18 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=18)
        card.state = DOING
        card.save()
        self.assertExitedStateNTimesRecently(2, card, TESTING, mocked_now.return_value)
        self.assertEnteredStateNTimesRecently(3, card, DOING, mocked_now.return_value)

        # Now move it back to TESTING again again 17 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=17)
        card.state = TESTING
        card.save()
        self.assertExitedStateNTimesRecently(3, card, DOING, mocked_now.return_value)
        self.assertEnteredStateNTimesRecently(3, card, TESTING, mocked_now.return_value)

        # Now move it to DEPLOYING 16 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=16)
        card.state = DEPLOYING
        card.save()
        self.assertExitedStateNTimesRecently(3, card, TESTING, mocked_now.return_value)
        self.assertEnteredStateOnceAt(card, DEPLOYING, mocked_now.return_value)

        # Now move it to DONE 16 days ago
        mocked_now.return_value = datetime.now() - relativedelta(days=16)
        card.state = DONE
        card.save()
        self.assertExitedStateOnceAt(card, DEPLOYING, mocked_now.return_value)
        self.assertEnteredStateOnceAt(card, DONE, mocked_now.return_value)
