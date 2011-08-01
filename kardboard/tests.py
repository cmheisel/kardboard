import datetime
import random
import os
import copy
import logging

import unittest2
from mock import patch
from dateutil.relativedelta import relativedelta

from kardboard.util import slugify


class KardboardTestCase(unittest2.TestCase):
    def setUp(self):
        if os.environ.get('KARDBOARD_SETTINGS'):
            os.environ['KARDBOARD_SETTINGS'] = ''
        import kardboard
        from flaskext.mongoengine import MongoEngine

        kardboard.app.config.from_object('kardboard.default_settings')
        kardboard.app.config['MONGODB_DB'] = 'kardboard-unittest'
        kardboard.app.config['DEBUG'] = True
        kardboard.app.config['TESTING'] = True
        kardboard.app.config['CELERY_ALWAYS_EAGER'] = True
        kardboard.app.db = MongoEngine(kardboard.app)

        self._flush_db()

        self.config = kardboard.app.config
        self.app = kardboard.app.test_client()
        self.flask_app = kardboard.app

        self.used_keys = []
        self._setup_logging()
        super(KardboardTestCase, self).setUp()

    def tearDown(self):
        if hasattr(self.config, 'TICKET_HELPER'):
            del self.config['TICKET_HELPER']

        self.flask_app.logger.handlers = self._old_logging_handlers

    def _setup_logging(self):
        self._old_logging_handlers = self.flask_app.logger.handlers
        del self.flask_app.logger.handlers[:]
        new_handler = logging.StreamHandler()
        new_handler.setLevel(logging.CRITICAL)
        new_handler.setFormatter(logging.Formatter(self.flask_app.debug_log_format))
        self.flask_app.logger.addHandler(new_handler)

    def _flush_db(self):
        from mongoengine.connection import _get_db
        db = _get_db()
        #Truncate/wipe the test database
        names = [name for name in db.collection_names() \
            if 'system.' not in name]
        [db.drop_collection(name) for name in names]

    def _get_target_url(self):
        raise NotImplementedError

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

    def _make_unique_key(self):
        key = random.randint(1, 10000)
        if key not in self.used_keys:
            self.used_keys.append(key)
            return key
        return self._make_unique_key()

    def make_card(self, **kwargs):
        key = self._make_unique_key()
        fields = {
            'key': "CMSAD-%s" % key,
            'title': "Theres always money in the banana stand",
            'backlog_date': datetime.datetime.now()
        }
        fields.update(**kwargs)
        k = self._get_card_class()(**fields)
        return k

    def make_board(self, **kwargs):
        key = self._make_unique_key()
        fields = {
            'name': "Teamocil Board %s" % (key, ),
            'categories':
                ["Numbness", "Short-term memory loss", "Reduced sex-drive"],
        }
        fields.update(**kwargs)
        b = self._get_board_class()(**fields)
        return b


class UtilTests(unittest2.TestCase):
    def test_business_days(self):
        from kardboard.util import business_days_between

        wednesday = datetime.datetime(year=2011, month=6, day=1)
        next_wednesday = datetime.datetime(year=2011, month=6, day=8)
        result = business_days_between(wednesday, next_wednesday)
        self.assertEqual(result, 5)

        aday = datetime.datetime(year=2011, month=6, day=1)
        manydayslater = datetime.datetime(year=2012, month=6, day=1)
        result = business_days_between(aday, manydayslater)
        self.assertEqual(result, 262)

    def test_month_range(self):
        from kardboard.util import month_range

        today = datetime.datetime(year=2011, month=6, day=12)
        start, end = month_range(today)
        self.assertEqual(6, start.month)
        self.assertEqual(1, start.day)
        self.assertEqual(2011, start.year)

        self.assertEqual(6, end.month)
        self.assertEqual(30, end.day)
        self.assertEqual(2011, end.year)

    def test_week_range(self):
        from kardboard.util import week_range
        today = datetime.datetime(year=2011, month=5, day=12)
        start, end = week_range(today)

        self.assertEqual(5, start.month)
        self.assertEqual(8, start.day)
        self.assertEqual(2011, start.year)

        self.assertEqual(5, end.month)
        self.assertEqual(14, end.day)
        self.assertEqual(2011, end.year)

        today = datetime.datetime(year=2011, month=6, day=5)
        start, end = week_range(today)
        self.assertEqual(6, start.month)
        self.assertEqual(5, start.day)
        self.assertEqual(2011, start.year)

        self.assertEqual(6, end.month)
        self.assertEqual(11, end.day)
        self.assertEqual(2011, end.year)


class BoardTests(KardboardTestCase):
    def _get_target_class(self):
        return self._get_board_class()

    def _make_one(self, **kwargs):
        return self.make_board(**kwargs)

    def test_valid_board(self):
        b = self._make_one()
        b.save()
        self.assert_(b.id)

    def test_board_slug(self):
        b = self._make_one(name="Operation Hot Mother")
        b.save()
        expected = u"operation-hot-mother"
        self.assertEqual(expected, b.slug)


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

        self.done_card2 = self._make_one()
        self.done_card2.backlog_date = datetime.datetime(
            year=2011, month=5, day=2)
        self.done_card2.start_date = datetime.datetime(
            year=2011, month=5, day=9)
        self.done_card2.done_date = datetime.datetime(
            year=2011, month=5, day=15)
        self.done_card2.save()

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

    def test_state_if_done(self):
        states = self.config.get('STATES')
        k = self._make_one()
        k.done_date = None
        k.state = states[-2]
        k.save()

        k.done_date = datetime.datetime.now()
        k.save()
        self.assertEqual(states[-1], k.state)

    def test_done_cycle_time(self):
        self.assertEquals(25, self.done_card.cycle_time)
        self.assertEquals(25, self.done_card._cycle_time)

    def test_done_lead_time(self):
        self.assertEquals(30, self.done_card.lead_time)
        self.assertEquals(30, self.done_card._lead_time)

    def test_wip_cycle_time(self):
        today = datetime.datetime(year=2011, month=6, day=12)

        self.assertEquals(None, self.wip_card.cycle_time)
        self.assertEquals(None, self.wip_card._cycle_time)

        self.assertEquals(None, self.wip_card.lead_time)
        self.assertEquals(None, self.wip_card._lead_time)

        actual = self.wip_card.current_cycle_time(
                today=today)
        self.assertEquals(25, actual)

    def test_elabo_cycle_time(self):
        today = datetime.datetime(year=2011, month=6, day=12)

        self.assertEquals(None, self.elabo_card.cycle_time)
        self.assertEquals(None, self.elabo_card._cycle_time)

        self.assertEquals(None, self.elabo_card.lead_time)
        self.assertEquals(None, self.elabo_card._lead_time)

        actual = self.elabo_card.current_cycle_time(
                today=today)
        self.assertEquals(None, actual)

    def test_backlogged(self):
        klass = self._get_target_class()
        now = datetime.datetime(2011, 6, 12)
        qs = klass.backlogged(now)
        self.assertEqual(1, qs.count())
        self.assertEqual(self.elabo_card.key, qs[0].key)

    def test_in_progress_manager(self):
        klass = self._get_target_class()
        now = datetime.datetime(2011, 6, 12)
        self.assertEqual(1, klass.in_progress(now).count())

    def test_completed_in_month(self):
        klass = self._get_target_class()
        self.assertEqual(1,
            klass.objects.done_in_month(year=2011, month=6, day=30).count())

    def test_moving_cycle_time(self):
        klass = self._get_target_class()
        expected = klass.objects.done().average('_cycle_time')

        expected = int(round(expected))
        actual = klass.objects.moving_cycle_time(
            year=2011, month=6, day=12)
        self.assertEqual(expected, actual)

    def test_done_in_week(self):
        klass = self._get_target_class()
        expected = 1
        actual = klass.objects.done_in_week(
            year=2011, month=6, day=15)

        self.assertEqual(expected, actual.count())

    def test_ticket_system(self):
        from kardboard.tickethelpers import TicketHelper
        self.config['TICKET_HELPER'] = \
            'kardboard.tickethelpers.TestTicketHelper'

        k = self._make_one()
        h = k.ticket_system

        self.assertEqual(True, isinstance(h, TicketHelper))
        self.assert_(k.key in h.get_ticket_url())

    def test_ticket_system_update(self):
        k = self._make_one()
        self.assert_(k._ticket_system_data == {})
        self.assert_(k._ticket_system_updated_at is None)

        k.ticket_system.update()
        now = datetime.datetime.now()
        updated_at = k._ticket_system_updated_at
        diff = now - updated_at
        self.assert_(diff.seconds <= 1)


class JIRAHelperTests(KardboardTestCase):
    def setUp(self):
        super(JIRAHelperTests, self).setUp()
        from kardboard.mocks import MockJIRAClient, MockJIRAIssue
        self.card = self.make_card()
        self.config['JIRA_WSDL'] = 'http://jira.example.com'
        self.config['JIRA_CREDENTIALS'] = ('foo', 'bar')
        self.config['TICKET_HELPER'] = 'kardboard.tickethelpers.JIRAHelper'
        self.ticket = MockJIRAIssue()
        self.sudspatch = patch('suds.client.Client', MockJIRAClient)
        self.sudspatch.start()

    def tearDown(self):
        super(JIRAHelperTests, self).tearDown()
        self.sudspatch.stop()
        del self.config['JIRA_WSDL']

    def _get_target_class(self):
        from kardboard.tickethelpers import JIRAHelper
        return JIRAHelper

    def _make_one(self):
        klass = self._get_target_class()
        return klass(self.config, self.card)

    def test_update(self):
        k = self.card
        k.save()
        self.assert_(k._ticket_system_data == {})
        self.assert_(k._ticket_system_updated_at is None)

        k.ticket_system.update()
        k.reload()
        now = datetime.datetime.now()
        updated_at = k._ticket_system_updated_at
        diff = now - updated_at
        self.assert_(diff.seconds <= 1)

    def test_get_title(self):
        h = self._make_one()
        expected = self.ticket.summary
        actual = h.get_title()
        self.assertEqual(expected, actual)

    def test_get_ticket_url(self):
        h = self._make_one()
        expected = "%s/browse/%s" % (self.config['JIRA_WSDL'],
            self.card.key)
        actual = h.get_ticket_url()
        self.assertEqual(actual, expected)


class KardTimeMachineTests(KardboardTestCase):
    def setUp(self):
        super(KardTimeMachineTests, self).setUp()
        self._set_up_data()

    def _get_target_class(self):
        return self._get_card_class()

    def _make_one(self, **kwargs):
        return self.make_card(**kwargs)

    def _set_up_data(self):
        klass = self._get_target_class()

        # Simulate creating 5 cards and moving
        # some forward
        backlog_date = datetime.datetime(
            year=2011, month=5, day=30)
        for i in xrange(0, 5):
            c = self._make_one(backlog_date=backlog_date)
            c.save()

        cards = klass.objects.all()[:2]
        for c in cards:
            c.start_date = backlog_date.replace(day=31)
            c.save()

        for c in cards:
            c.done_date = backlog_date.replace(month=6, day=2)
            c.save()

    def test_time_machine(self):
        klass = self._get_target_class()

        backlogged_day = datetime.datetime(
            year=2011, month=5, day=30)
        started_2_day = datetime.datetime(
            year=2011, month=5, day=31)
        finished_2_day = datetime.datetime(
            year=2011, month=6, day=2)

        today = datetime.datetime(
            year=2011, month=6, day=12)

        expected = 2
        actual = klass.in_progress(today)
        self.assertEqual(expected, actual.count())

        expected = 0
        actual = klass.in_progress(backlogged_day)
        self.assertEqual(expected, actual.count())

        expected = 2
        actual = klass.in_progress(started_2_day)
        self.assertEqual(expected, actual.count())

        expected = 2
        actual = klass.in_progress(finished_2_day)
        self.assertEqual(expected, actual.count())


class DashboardTestCase(KardboardTestCase):
    def setUp(self):
        super(DashboardTestCase, self).setUp()

        from kardboard.models import Kard
        self.Kard = Kard
        self.year = 2011
        self.month = 6
        self.day = 15

        self.board = self.make_board()
        self.board1 = self.make_board()
        self.backlogged_date = datetime.datetime(
            year=self.year, month=self.month, day=12)

        for i in xrange(0, 5):
            #board will have 5 cards in elabo, started, and done
            k = self.make_card(backlog_date=self.backlogged_date)  # elabo
            k.save()
            self.board.cards.append(k)

            k = self.make_card(start_date=datetime.datetime(
                year=self.year, month=self.month, day=12))
            k.save()
            self.board.cards.append(k)

            k = self.make_card(
                start_date=datetime.datetime(year=self.year,
                    month=self.month, day=12),
                done_date=datetime.datetime(year=self.year,
                    month=self.month, day=19))
            k.save()
            self.board.cards.append(k)

            self.board.save()

        for i in xrange(0, 3):
            #board will have 3 cards in elabo, started, and done
            k = self.make_card(backlog_date=self.backlogged_date)  # backlogged
            k.save()
            self.board1.cards.append(k)

            k = self.make_card(start_date=datetime.datetime(
                year=2011, month=6, day=12))
            k.save()
            self.board1.cards.append(k)

            k = self.make_card(
                start_date=datetime.datetime(year=2011, month=6, day=12),
                done_date=datetime.datetime(year=2011, month=6, day=19))
            k.save()
            self.board1.cards.append(k)

            self.board1.save()


class StateTests(DashboardTestCase):
    def _get_target_url(self, state=None):
        base_url = '/state/'
        if state:
            state_slug = slugify(state)
            base_url = base_url + '%s/' % state_slug
        return base_url

    def test_state_page(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)


class HomepageTests(DashboardTestCase):
    def _get_target_url(self):
        # We have to specify a day, because otherwise just / would
        # be whatever day it is when you run the tests
        return '/%s/%s/%s/' % (self.year, self.month, self.day)

    def test_wip(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)
        date = datetime.datetime(self.year, self.month, self.day)

        expected_cards = list(self.Kard.backlogged(date)) + \
            list(self.Kard.in_progress(date))

        for c in expected_cards:
            self.assertIn(c.key, rv.data)


class DetailPageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/card/%s/' % self.card.key

    def setUp(self):
        super(DetailPageTests, self).setUp()
        self.card = self._get_card_class().objects.first()
        self.response = self.app.get(self._get_target_url())
        self.assertEqual(200, self.response.status_code)

    def test_data(self):
        expected_values = [
            self.card.title,
            self.card.key,
            self.card.backlog_date.strftime("%m/%d/%Y"),
            "Start date:",
            "Done date:",
            "/card/%s/edit/" % self.card.key,
            "/card/%s/delete/" % self.card.key,
        ]
        for v in expected_values:
            self.assertIn(v, self.response.data)


class MonthPageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/%s/%s/' % (self.year, self.month)

    def test_wip(self):
        from kardboard.util import month_range

        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        date = datetime.datetime(self.year, self.month, self.day)
        start, date = month_range(date)
        expected_cards = self.Kard.in_progress(date)

        for c in expected_cards:
            self.assertIn(c.key, rv.data)

        expected = """<p class="value">%s</p>""" % expected_cards.count()
        self.assertIn(expected, rv.data)

    def test_done_month_metric(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        done_month = self.Kard.objects.done_in_month(
            year=self.year, month=self.month)

        expected = """<p class="value">%s</p>""" % done_month.count()
        self.assertIn(expected, rv.data)

    def test_cycle_time_metric(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        cycle_time = self.Kard.objects.moving_cycle_time(
            year=self.year, month=self.month)

        expected = """<p class="value">%s</p>""" % cycle_time
        self.assertIn(expected, rv.data)


class DayPageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/%s/%s/%s/' % (self.year, self.month, self.day)

    def test_done_in_week_metric(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        done = self.Kard.objects.done_in_week(
            year=self.year, month=self.month, day=self.day).count()

        expected = """<p class="value">%s</p>""" % done
        self.assertIn(expected, rv.data)


class DonePageTests(DashboardTestCase):
    def _get_target_url(self):
        return '/done/'

    def test_done_page(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)

        done = self.Kard.objects.done()

        for c in done:
            self.assertIn(c.key, rv.data)


class DoneReportTests(DashboardTestCase):
    def _get_target_url(self):
        return '/done/report/%s/%s/' % (self.year, self.month)

    def test_done_report(self):
        rv = self.app.get(self._get_target_url())
        self.assertEqual(200, rv.status_code)
        self.assertIn("text/plain", rv.headers['Content-Type'])

        done = self.Kard.objects.done_in_month(
            month=self.month, year=self.year)

        for c in done:
            self.assertIn(c.key, rv.data)


class QuickJumpTests(DashboardTestCase):
    def _get_target_url(self, key):
        return '/quick/?key=%s' % (key, )

    def test_quick_existing(self):
        key = self.Kard.objects.first().key

        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)

        expected = "/card/%s/edit/" % (key, )
        self.assertIn(expected, res.headers['Location'])

    def test_quick_case_insenitive(self):
        key = self.Kard.objects.first().key
        lower_key = key.lower()

        res = self.app.get(self._get_target_url(lower_key))
        self.assertEqual(302, res.status_code)

        expected = "/card/%s/edit/" % (key.upper(), )
        self.assertIn(expected, res.headers['Location'])

    def test_quick_add(self):
        key = "CMSCMSCMS-127"
        res = self.app.get(self._get_target_url(key))
        self.assertEqual(302, res.status_code)
        expected = "/card/add/?key=%s" % (key, )
        self.assertIn(expected, res.headers['Location'])


class FormTests(KardboardTestCase):
    pass


class CardFormTest(FormTests):
    def setUp(self):
        from werkzeug.datastructures import MultiDict

        super(CardFormTest, self).setUp()
        self.Form = self._get_target_class()
        self.required_data = {
            'key': u'CMSIF-199',
            'title': u'You gotta lock that down',
            'backlog_date': u"06/11/2011",
            'category': u'Bug',
            'state': u'Doing',
        }
        self.post_data = MultiDict(self.required_data)

    def _get_target_class(self):
        from kardboard.forms import get_card_form
        return get_card_form(new=True)

    def test_required_fields(self):
        f = self.Form(self.post_data)
        f.validate()
        self.assertEquals(0, len(f.errors))

        card = self._get_card_class()()
        f.populate_obj(card)
        card.save()

    def test_datetime_coercing(self):
        f = self.Form(self.post_data)
        data = f.backlog_date.data
        self.assertEqual(6, data.month)

    def test_key_uniqueness(self):
        klass = self._get_card_class()
        c = klass(**self.required_data)
        c.backlog_date = datetime.datetime.now()
        c.save()

        f = self.Form(self.post_data)
        f.validate()
        self.assertIn('key', f.errors.keys())


class CardCRUDTests(KardboardTestCase):
    def setUp(self):
        super(CardCRUDTests, self).setUp()
        self.required_data = {
            'key': u'CMSIF-199',
            'title': u'You gotta lock that down',
            'backlog_date': u"06/11/1911",
            'category': u'Bug',
            'state': u'Todo',
        }
        self.config['TICKET_HELPER'] = \
            'kardboard.tickethelpers.TestTicketHelper'

    def tearDown(self):
        super(CardCRUDTests, self).tearDown()

    def _get_target_url(self):
        return '/card/add/'

    def _get_target_class(self):
        return self._get_card_class()

    def test_add_card(self):
        klass = self._get_target_class()

        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)

        res = self.app.post(self._get_target_url(),
            data=self.required_data)

        self.assertEqual(302, res.status_code)
        self.assertEqual(1, klass.objects.count())

        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)

    def test_add_card_with_qs_params(self):
        key = "CMSCMS-127"
        url = "%s?key=%s" % (self._get_target_url(), key)
        res = self.app.get(url)
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)
        self.assertIn('value="%s"' % (key, ), res.data)

    def test_add_card_with_no_title(self):
        klass = self._get_target_class()

        data = copy.copy(self.required_data)
        del data['title']

        res = self.app.post(self._get_target_url(),
            data=data)

        self.assertEqual(302, res.status_code)
        self.assertEqual(1, klass.objects.count())

        # This should work because we mocked TestHelper
        # in setUp
        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)
        self.assertEqual(k.title, "Dummy Title from Dummy Ticket System")

    def test_add_duplicate_card(self):
        klass = self._get_target_class()
        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn('<form', res.data)

        res = self.app.post(self._get_target_url(),
            data=self.required_data)

        self.assertEqual(200, res.status_code)

    def test_edit_card(self):
        klass = self._get_target_class()

        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        target_url = "/card/%s/edit/" % (card.key, )
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)
        self.assertIn(card.key, res.data)
        self.assertIn(card.title, res.data)

        res = self.app.post(target_url,
            data=self.required_data)

        k = klass.objects.get(key=self.required_data['key'])
        self.assert_(k.id)
        self.assertEqual(302, res.status_code)
        self.assertEqual(1, klass.objects.count())
        self.assertEqual(6, k.backlog_date.month)
        self.assertEqual(11, k.backlog_date.day)
        self.assertEqual(1911, k.backlog_date.year)

    def test_delete_card(self):
        klass = self._get_target_class()

        card = klass(**self.required_data)
        card.backlog_date = datetime.datetime.now()
        card.save()

        target_url = "/card/%s/delete/" % (card.key, )
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)
        self.assertIn('value="Cancel"', res.data)
        self.assertIn('value="Delete"', res.data)
        self.assert_(klass.objects.get(key=card.key))

        res = self.app.post(target_url, data={'cancel': 'Cancel'})
        self.assertEqual(302, res.status_code)
        self.assert_(klass.objects.get(key=card.key))

        res = self.app.post(target_url, data={'delete': 'Delete'})
        self.assertEqual(302, res.status_code)


class ExportTests(KardboardTestCase):
    def _get_target_url(self):
        return '/card/export/'

    def setUp(self):
        super(ExportTests, self).setUp()
        for i in xrange(0, 10):
            c = self.make_card()
            c.save()

    def test_csv(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)
        self.assertIn("text/plain", res.headers['Content-Type'])

        Kard = self._get_card_class()
        for k in Kard.objects.all():
            self.assertIn(k.key, res.data)


class ChartIndexTests(KardboardTestCase):
    def _get_target_url(self):
        return '/chart/'

    def test_chart_index(self):
        res = self.app.get(self._get_target_url())
        self.assertEqual(200, res.status_code)


class ThroughputChartTests(KardboardTestCase):
    def _get_target_url(self, months=None):
        base_url = '/chart/throughput/'
        if months:
            base_url = base_url = "%s/" % months
        return base_url

    def test_throughput(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)


class CycleTimeHistoryTests(KardboardTestCase):

    def _get_target_url(self, months=None, date=None):
        base_url = '/chart/cycle/'
        if months:
            base_url = base_url + "%s/" % months
        if date:
            base_url = base_url + "from/%s/%s/%s/" % \
                (date.year, date.month, date.day)
        return base_url

    def test_cycle(self):
        date = datetime.datetime(year=2011, month=7, day=1)
        end_date = date - relativedelta(months=6)
        target_url = self._get_target_url(date=date)
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)

        expected = end_date.strftime("%m/%d/%Y")
        self.assertIn(expected, res.data)


class CumulativeFlowTests(KardboardTestCase):
    def _get_target_url(self, months=None):
        base_url = '/chart/flow/'
        if months:
            base_url = base_url = "%s/" % months
        return base_url

    def test_cycle(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)


class RobotsTests(KardboardTestCase):
    def _get_target_url(self):
        return '/robots.txt'

    def test_robots(self):
        target_url = self._get_target_url()
        res = self.app.get(target_url)
        self.assertEqual(200, res.status_code)


if __name__ == "__main__":
    unittest2.main()
