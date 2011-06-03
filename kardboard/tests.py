import datetime
import random

import unittest2


class KardboardTestCase(unittest2.TestCase):
    def setUp(self):
        import kardboard
        from flaskext.mongoengine import MongoEngine

        kardboard.app.config['MONGODB_DB'] = 'kardboard-unittest'
        kardboard.app.db = MongoEngine(kardboard.app)

        self._flush_db()

        self.app = kardboard.app.test_client()
        super(KardboardTestCase, self).setUp()

    def _flush_db(self):
        from mongoengine.connection import _get_db
        db = _get_db()
        #Truncate/wipe the test database
        names = [name for name in db.collection_names() \
            if 'system.' not in name]
        [db.drop_collection(name) for name in names]

    def _get_target_class(self):
        raise NotImplementedError

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def _get_card_class(self):
        from kardboard.models import Kard
        return Kard

    def _get_board_class(self):
        from kardboard.models import Board
        return Board

    def make_card(self, **kwargs):
        key = random.randint(1, 100)
        required_fields = {
            'key': "CMSAD-%s" % key,
            'title': "There's always money in the banana stand",
            'backlog_date': datetime.datetime.now()
        }
        kwargs.update(required_fields)
        k = self._get_card_class()(**kwargs)
        return k

    def make_board(self, **kwargs):
        required_fields = {
            'name': "Teamocil",
            'categories':
                ["Numbness", "Short-term memory loss", "Reduced sex-drive"],
        }
        kwargs.update(required_fields)
        b = self._get_board_class()(**kwargs)
        return b


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


class BoardTests(KardboardTestCase):
    def _get_target_class(self):
        return self._get_board_class()

    def _make_one(self, **kwargs):
        return self.make_board(**kwargs)

    def test_valid_board(self):
        b = self._make_one()
        b.save()
        self.assert_(b.id)


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

        self.wip_card = self._make_one(key="CMSLUCILLE-2")
        self.wip_card.backlog_date = datetime.datetime(
            year=2011, month=5, day=2)
        self.wip_card.start_date = datetime.datetime(
            year=2011, month=5, day=9)
        self.wip_card.save()

        self.elabo_card = self._make_one(key="GOB-1")
        self.elabo_card.backlog_date = datetime.datetime(
            year=2011, month=5, day=2)
        self.elabo_card.save()

    def _get_target_class(self):
        return self._get_card_class()

    def _make_one(self, **kwargs):
        return self.make_card(**kwargs)

    def test_valid_card(self):
        k = self._make_one()
        k.save()
        self.assert_(k.id)

    def test_done_cycle_time(self):
        self.assertEquals(26, self.done_card.cycle_time)
        self.assertEquals(26, self.done_card._cycle_time)

    def test_done_lead_time(self):
        self.assertEquals(31, self.done_card.lead_time)
        self.assertEquals(31, self.done_card._lead_time)

    def test_wip_cycle_time(self):
        today = datetime.datetime(year=2011, month=6, day=12)

        self.assertEquals(None, self.wip_card.cycle_time)
        self.assertEquals(None, self.wip_card._cycle_time)

        self.assertEquals(None, self.wip_card.lead_time)
        self.assertEquals(None, self.wip_card._lead_time)

        actual = self.wip_card.current_cycle_time(
                today=today)
        self.assertEquals(26, actual)

    def test_elabo_cycle_time(self):
        today = datetime.datetime(year=2011, month=6, day=12)

        self.assertEquals(None, self.elabo_card.cycle_time)
        self.assertEquals(None, self.elabo_card._cycle_time)

        self.assertEquals(None, self.elabo_card.lead_time)
        self.assertEquals(None, self.elabo_card._lead_time)

        actual = self.elabo_card.current_cycle_time(
                today=today)
        self.assertEquals(None, actual)


class HomepageTests(KardboardTestCase):
    pass


if __name__ == "__main__":
    unittest2.main()
