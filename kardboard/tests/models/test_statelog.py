from kardboard.tests.core import ModelTestCase


class StateLogTests(ModelTestCase):
    def _get_class(self):
        from kardboard.models.statelog import StateLog
        return StateLog

    def make_one(self, **kwargs):
        from kardboard.util import now

        key = self.make_unique_key()
        values = {
            'card': "DEFAULT-%s" % key,
            'state': "Todo",
            'entered_at': now()
        }
        values.update(kwargs)
        return super(StateLogTests, self).make_one(**values)

    def test_created_at(self):
        from kardboard.util import now

        sl = self.make_one()
        sl.save()
        self.assertEqualDateTimes(now(), sl.created_at)

    def test_updated_at(self):
        from kardboard.util import now

        sl = self.make_one()
        sl.save()
        self.assertEqualDateTimes(now(), sl.updated_at)

    def test_duration_if_entered(self):
        sl = self.make_one()
        self.assertEqual(0, sl.duration)

    def test_duration_if_exited(self):
        from kardboard.util import relativedelta, now

        sl = self.make_one(
            exited_at=now() + relativedelta(hours=6)
        )
        self.assertEqual(6.0, sl.duration)

    def test_exited_at_must_be_greater_than_entered(self):
        from kardboard.util import relativedelta, now
        from mongoengine import ValidationError

        sl = self.make_one(
            exited_at=now() - relativedelta(hours=1)
        )

        self.assertRaises(ValidationError, sl.save)

    def test_str(self):
        sl = self.make_one()
        self.assert_(str(sl))
