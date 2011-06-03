import datetime
import unittest2


class KardboardTestCase(unittest2.TestCase):
    def setUp(self):
        import kardboard
        kardboard.app.config['MONGODB_DB'] = 'kardboard-unittest'
        self.app = kardboard.app.test_client()

    def tearDown(self):
        from mongoengine.connection import _get_db
        db = _get_db()
        #Truncate/wipe the test database
        [db.drop_collection(name) for name in db.collection_names() \
            if 'system.' not in name]

    def _get_target_class(self):
        raise NotImplementedError

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)


class UtilTests(unittest2.TestCase):
    def test_business_days(self):
        from kardboard.util import business_days_between

        wednesday = datetime.datetime(year=2011, month=6, day=1)
        next_wednesday = datetime.datetime(year=2011, month=6, day=8)
        result = business_days_between(wednesday, next_wednesday)
        self.assertEqual(result, 6)

        aday = datetime.datetime(year=2011, month=6, day=1)
        manydayslater = datetime.datetime(year=2012, month=6, day=1)
        result = business_days_between(aday, manydayslater)
        self.assertEqual(result, 263)


class KardTests(KardboardTestCase):
    def setUp(self):
        super(KardTests, self).setUp()
        self.done_card = self._make_one()
        self.done_card.backlog_date = datetime.datetime(
            year=2011, month=5, day=2)
        self.done_card.start_date = datetime.datetime(
            year=2011, month=5, day=9)
        self.done_card.done_date = datetime.datetime(
            year=2011, month=6, day=12)
        self.done_card.save()

    def _get_target_class(self):
        from kardboard.models import Kard
        return Kard

    def _make_one(self, **kwargs):
        required_fields = {
            'key': "CMSAD-1",
            'title': "There's always money in the banana stand",
            'backlog_date': datetime.datetime.now()
        }
        kwargs.update(required_fields)
        k = self._get_target_class()(**kwargs)
        return k

    def test_valid_card(self):
        k = self._make_one()
        k.save()
        self.assert_(k.id)

    def test_cycle_time(self):
        self.assertEquals(26, self.done_card.cycle_time)
        self.assertEquals(26, self.done_card._cycle_time)

    def test_lead_time(self):
        self.assertEquals(31, self.done_card.lead_time)
        self.assertEquals(31, self.done_card._lead_time)

if __name__ == "__main__":
    unittest2.main()
