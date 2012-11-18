from kardboard.tests.core import ModelTestCase


class CardTests(ModelTestCase):
    def _get_class(self):
        from kardboard.models.card import Card
        return Card

    def make_one(self, **kwargs):
        key = self.make_unique_key()
        values = {
            'title': 'Default title',
            'key': 'DEFAULT-%s' % key,
            'teams': ['Team 1', 'Team 2', ]
        }
        values.update(kwargs)
        return super(CardTests, self).make_one(**values)

    def assertEqualStates(self, expected, actual):
        datetimes = []

        keys = expected.keys()

        for key, value in expected.items():
            if key in ("entered_at", "exited_at"):
                pass
            msg = "%s: Actual: %s != Expected: %s" % (
                key, value, actual[key])
            self.assertEqual(value, actual[key], msg=msg)

        if 'entered_at' in keys:
            datetimes.append((expected['entered_at'], actual['entered_at']))
        if 'exited_at' in keys:
            datetimes.append((expected['exited_at'], actual['exited_at']))

        for expecteddt, actualdt in datetimes:
            self.assertEqualDateTimes(expecteddt, actualdt)

    def test_set_state(self):
        c = self.make_one()
        c.save()

        new_state = {
            'card': c.key,
            'state': "Backlog",
        }
        c.set_state(**new_state)

        self.assertEqualStates(
            new_state,
            c.current_state)

    def test_default_state(self):
        c = self.make_one()
        c.save()

        expected_current_state = {
            'state': "Backlog",
            'blocked': False,
        }

        self.assertEqualStates(
            expected_current_state,
            c.current_state)

    def test_setting_state_on_a_new_ticket(self):
        c = self.make_one()
        c.set_state(state='Elaboration')
        c.save()

        self.assertEqualStates(
            {'state': 'Elaboration'},
            c.current_state)

    def test_setting_state_flow(self):
        from kardboard.util import relativedelta, now
        c = self.make_one()
        c.set_state(state='Backlog',
            entered_at=now() - relativedelta(hours=1))
        c.save()

        c.title = "Changing the title"
        c.save()

        c.set_state(state="Elaboration",
            entered_at=now() + relativedelta(hours=2))
        c.save()

        self.assertEqual(2, len(c.state_log))

    def test_state_log_ordering(self):
        from kardboard.util import relativedelta, now
        c = self.make_one()
        c.set_state(state='Backlog',
            entered_at=now() - relativedelta(hours=1))
        c.save()

        c.set_state(state="Elaboration",
            entered_at=now() + relativedelta(hours=2))
        c.save()

        expected = ["Backlog", "Elaboration"]
        actual = [sl['state'] for sl in c.state_log]
        self.assertEqual(expected, actual)

    def test_state_log_auto_exit_set(self):
        from kardboard.util import relativedelta, now
        c = self.make_one()
        c.set_state(state='Backlog',
            entered_at=now() - relativedelta(hours=1))
        c.save()

        c.set_state(state="Elaboration",
            entered_at=now() + relativedelta(hours=2))
        c.save()

        self.assert_(c.state_log[0]['exited_at'])

    def test_state_log_auto_exit_set_with_several_state_changes(self):
        from kardboard.util import relativedelta, now
        c = self.make_one()
        c.set_state(state='Backlog',
            entered_at=now() - relativedelta(hours=1))
        c.save()

        c.set_state(state="Elaboration",
            entered_at=now() + relativedelta(hours=2))
        c.save()

        c.set_state(state="Ready to Build",
            entered_at=now() + relativedelta(hours=3))
        c.save()

        c.set_state(state="Building",
            entered_at=now() + relativedelta(hours=4),
            exited_at=now() + relativedelta(hours=5))
        c.save()

        for sl in c.state_log:
            self.assert_(sl['exited_at'])


class CardBlockingTest(CardTests):
    def test_blocked_card_shows_it(self):
        c = self.make_one()
        c.save()
        c.block("Test")

        self.assertEqual(True, c.blocked)

    def test_blocked_card_has_reason(self):
        c = self.make_one()
        c.save()
        c.block("Lego")


        self.assertEqual(c.blocker['message'], "Lego")

    def test_blocked_card_has_duration(self):
        from kardboard.util import relativedelta, now

        c = self.make_one()
        c.save()
        c.block(
            "Test",
            blocked_at=now() - relativedelta(hours=3)
        )

        self.assertEqual(c.blocker['duration'], 3)

    def test_unblocking_card(self):
        c = self.make_one()
        c.save()
        c.block("Test")
        c.unblock()

        self.assertEqual(False, c.blocked)

    def test_unblocking_card_duration(self):
        from kardboard.util import relativedelta, now

        c = self.make_one()
        c.save()
        c.block(
            "Test",
            blocked_at=now() - relativedelta(hours=3)
        )
        c.unblock(
            unblocked_at=now() + relativedelta(hours=1)
        )

        self.assertEqual(c.blocker['duration'], 4)

