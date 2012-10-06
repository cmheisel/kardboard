#!/usr/bin/env python

import datetime
import random
import os
import logging

import unittest2
from dateutil.relativedelta import relativedelta


class KardboardTestCase(unittest2.TestCase):
    def setUp(self):
        if os.environ.get('KARDBOARD_SETTINGS'):
            os.environ['KARDBOARD_SETTINGS'] = ''

        from kardboard import default_settings
        default_settings.TEMPLATE_DEBUG = True
        from kardboard.views import app
        from flask.ext.mongoengine import MongoEngine

        app.config.from_object('kardboard.default_settings')
        app.config['MONGODB_DB'] = 'kardboard-unittest'
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['CELERY_ALWAYS_EAGER'] = True
        app.db = MongoEngine(app)

        self._flush_db()

        self.config = app.config
        self.app = app.test_client()
        self.flask_app = app

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

    def _get_record_class(self):
        from kardboard.models import DailyRecord
        return DailyRecord

    def _get_person_class(self):
        from kardboard.models import Person
        return Person

    def _make_unique_key(self):
        key = random.randint(1, 10000)
        if key not in self.used_keys:
            self.used_keys.append(key)
            return key
        return self._make_unique_key()

    def _date(self, dtype, date=None, days=0):
        from kardboard.util import make_end_date, make_start_date
        from kardboard.util import now

        if not date:
            date = now()

        if dtype == 'start':
            date = make_start_date(date=date)
        elif dtype == 'end':
            date = make_end_date(date=date)

        date = date + relativedelta(days=days)
        return date

    def make_card(self, **kwargs):
        from kardboard.util import now
        key = self._make_unique_key()
        fields = {
            'key': "CMSAD-%s" % key,
            'title': "Theres always money in the banana stand",
            'backlog_date': now()
        }
        fields.update(**kwargs)
        k = self._get_card_class()(**fields)
        return k

    def delete_all_cards(self):
        self._get_card_class().objects.all().delete()

    def make_record(self, date, **kwargs):
        fields = {
            'date': date,
            'backlog': 3,
            'in_progress': 8,
            'done': 10,
            'completed': 1,
            'moving_cycle_time': 12,
            'moving_lead_time': 16,
        }
        fields.update(**kwargs)
        r = self._get_record_class()(**fields)
        return r

    def make_person(self, **kwargs):
        key = self._make_unique_key()
        fields = {
            'name': 'cheisel-%s' % key,
        }
        fields.update(**kwargs)
        p = self._get_person_class()(**fields)
        return p


class DashboardTestCase(KardboardTestCase):
    def setUp(self):
        super(DashboardTestCase, self).setUp()

        from kardboard.models import Kard, DailyRecord
        self.Kard = Kard
        self.DailyRecord = DailyRecord
        self.year = datetime.datetime.now().year
        self.month = 6
        self.day = 15

        self.team1 = self.config['CARD_TEAMS'][0]
        self.team2 = self.config['CARD_TEAMS'][1]

        self.backlogged_date = datetime.datetime(
            year=self.year, month=self.month, day=12)

        for i in xrange(0, 5):
            #board will have 5 cards in elabo, started, and done
            k = self.make_card(backlog_date=self.backlogged_date, team=self.team1)  # elabo
            k.save()

            k = self.make_card(start_date=datetime.datetime(
                year=self.year, month=self.month, day=12), team=self.team1)
            k.save()

            k = self.make_card(
                start_date=datetime.datetime(year=self.year,
                    month=self.month, day=12),
                done_date=datetime.datetime(year=self.year,
                    month=self.month, day=19), team=self.team1)
            k.save()

        for i in xrange(0, 3):
            #board will have 3 cards in elabo, started, and done
            k = self.make_card(backlog_date=self.backlogged_date, team=self.team2)  # backlogged
            k.save()

            k = self.make_card(start_date=datetime.datetime(
                year=2011, month=6, day=12), team=self.team2)
            k.save()

            k = self.make_card(
                start_date=datetime.datetime(year=2011, month=6, day=12),
                done_date=datetime.datetime(year=2011, month=6, day=19), team=self.team2)
            k.save()

    def _set_up_records(self):
        from kardboard.util import make_start_date
        from kardboard.util import make_end_date

        start_date = datetime.datetime(2011, 1, 1)
        end_date = datetime.datetime(2011, 6, 30)

        start_date = make_start_date(date=start_date)
        end_date = make_end_date(date=end_date)

        current_date = start_date
        while current_date <= end_date:
            r = self.make_record(current_date)
            r.save()
            current_date = current_date + relativedelta(days=1)


class FormTests(KardboardTestCase):
    pass
