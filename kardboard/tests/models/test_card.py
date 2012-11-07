from ..core import ModelTestCase


class CardTests(ModelTestCase):
    def _get_class(self):
        from ...models.card import Card
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

        if 'entered_at' in expected.keys():
            datetimes.append((expected['entered_at'], actual['entered_at']))
            del expected['entered_at']
            del actual['entered_at']
        if 'exited_at' in expected.keys():
            datetimes.append((expected['exited_at'], actual['exited_at']))
            del expected['exited_at']
            del actual['exited_at']

        for key, value in expected.items():
            msg = "%s: Actual: %s != Expected: %s" % (
                key, value, actual[key])
            self.assertEqual(value, actual[key], msg=msg)

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

    def ztest_default_state(self):
        c = self.make_one()
        c.save()

        expected_current_state = {
            'state': "Backlog",
            'blocked': False,
        }

        self.assertEqualStates(
            c.current_state,
            expected_current_state)

    def ztest_set_current_state(self):
        from ...util import now

        c = self.make_one()
        c.save()

        new_current_state = {
            'state': "Backlog",
            'entered_at': now(),
            'exited_at': None,
            'blocked': True,
            'message': "Waiting on dependent ticket before it can be pulled",
        }
        c.current_state = new_current_state
        c.save()

        self.assertEqualStates(
            c.current_state,
            new_current_state)
