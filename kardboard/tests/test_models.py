import datetime
from copy import deepcopy

from dateutil.relativedelta import relativedelta

from kardboard.tests.core import KardboardTestCase


class DisplayBoardTests(KardboardTestCase):
    def setUp(self):
        super(DisplayBoardTests, self).setUp()
        self.config['TICKET_HELPER'] = 'kardboard.tickethelpers.TestTicketHelper'

        self.Kard = self._get_card_class()

        self.start_date = self._date('start', )

        from kardboard.models import States
        self.states = States()
        self.teams = self.config.get('CARD_TEAMS')
        self._set_up_cards()

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

    def _set_up_cards(self):
        team1 = self.teams[0]
        team2 = self.teams[1]

        self._make_a_teams_cardset(team1, 4)
        self._make_a_teams_cardset(team2, 2)

    def _make_a_teams_cardset(self, team, num_cards):
        backlog_date = self._date('start', days=-10)
        start_date = self._date('start', days=-5)
        done_date = self._date('end')

        for i in xrange(0, num_cards):
            c = self.make_card(
                backlog_date=backlog_date,
                team=team,
                state=self.states.backlog,
            )
            c.save()

            c = self.make_card(
                backlog_date=backlog_date,
                start_date=start_date,
                team=team,
                state=self.states.start,
            )
            c.save()

            c = self.make_card(
                backlog_date=backlog_date,
                start_date=start_date,
                done_date=done_date,
                team=team,
                state=self.states.done,
            )
            c.save()

            # Really old cards
            c = self.make_card(
                backlog_date=self._date('start', days=-30),
                start_date=self._date('start', days=-25),
                done_date=self._date('start', days=-20),
                team=team,
                state=self.states.done,
            )
            c.save()

    def _get_target_class(self):
        from kardboard.models import DisplayBoard
        return DisplayBoard

    def test_defaults(self):
        board = self._make_one()

        backlogged = self.Kard.backlogged()
        in_progress = self.Kard.in_progress()
        done = self.Kard.objects.done().filter(
            done_date__gte=self._date('end', days=-7)
        )

        expected = backlogged.count() + in_progress.count() + done.count()

        self.assertEqual(expected, len(board.cards))

        rows = list(board.rows)  # It's a generator
        self.assertEqual(2, len(rows))
        self.assertEqual(self.teams[0], rows[0][0]['label'])
        self.assertEqual(4, len(rows[0][1]['cards']))

    def test_column_counts(self):
        board = self._make_one()

        expected = (
            ('Team', None),
            ('Todo', 6),
            ('Doing', 6),
            ('Done', 6),
        )
        actual = board.headers
        self.assertEqual(actual, expected)

    def test_backlog_sorting(self):
        self.delete_all_cards()
        team1 = self.teams[0]
        backlog_date = self._date('start', days=-10)
        versions = [None, "1.2.1-c", "1.2.1"]
        for v in versions:
            c = self.make_card(
                backlog_date=backlog_date,
                team=team1,
                state=self.states.backlog,
                _version=v,
            )
            assert c._version == v
            c.save()
            assert c._version == v

        board = self._make_one()
        rows = list(board.rows)
        backlog = rows[0][1]['cards']

        expected = ['1.2.1', '1.2.1-c', None]
        actual = [c._version for c in backlog]
        self.assertEqual(expected, actual)



class StatesTests(KardboardTestCase):
    def setUp(self):
        super(StatesTests, self).setUp()
        self.old_config = deepcopy(self.config)
        self.config['CARD_STATES'] = (
            'Backlog',
            'In Progress',
            'Deploy',
            'Done',
        )

        nondefault_keys = [
            'BACKLOG_STATE',
            'START_STATE',
            'DONE_STATE',
        ]
        for key in nondefault_keys:
            if key in self.config.keys():
                del(self.config[key])

    def tearDown(self):
        self.config = deepcopy(self.old_config)

    def _get_target_class(self):
        from kardboard.models import States
        return States

    def test_iteration(self):
        states = self._make_one()
        expected = [state for state in self.config['CARD_STATES']]
        actual = [state for state in states]
        self.assertEqual(expected, actual)

    def test_default_state_groups(self):
        states = self._make_one()
        expected = 'Backlog'
        self.assertEqual(expected, states.backlog)
        self.assertEqual([expected, ], states.pre_start)

        expected = 'In Progress'
        self.assertEqual(expected, states.start)

        expected = ['In Progress', 'Deploy']
        self.assertEqual(expected, states.in_progress)

        expected = 'Done'
        self.assertEqual(expected, states.done)

    def test_configured_state_groups(self):
        self.config['CARD_STATES'] = (
            'Backlog',
            'Planning',
            'In Progress',
            'Testing',
            'Deploy',
            'Done',
            'Archive',
        )
        self.config['BACKLOG_STATE'] = 0
        self.config['START_STATE'] = 2
        self.config['DONE_STATE'] = -2

        states = self._make_one()

        expected = ['Backlog', 'Planning']
        self.assertEqual(expected[0], states.backlog)
        self.assertEqual(expected, states.pre_start)

        expected = 'In Progress'
        self.assertEqual(expected, states.start)

        expected = ['In Progress', 'Testing', 'Deploy']
        self.assertEqual(expected, states.in_progress)

        expected = 'Done'
        self.assertEqual(expected, states.done)

    def test_for_forms(self):
        states = self._make_one()

        expected = (
            ('', ''),
            ('Backlog', 'Backlog'),
            ('In Progress', 'In Progress'),
            ('Deploy', 'Deploy'),
            ('Done', 'Done'),
        )
        self.assertEqual(expected, states.for_forms)


class DailyRecordTests(KardboardTestCase):
    def setUp(self):
        super(DailyRecordTests, self).setUp()

        self.year = 2011
        self.month = 8
        self.day = 15

        self.date = datetime.datetime(
            year=self.year, month=self.month,
            day=self.day)
        self.date2 = self.date + relativedelta(days=7)
        self.date3 = self.date2 + relativedelta(days=14)

        self.dates = [self.date, self.date2, self.date3]

    def _set_up_days(self):
        k = self.make_card(
            backlog_date=self.date,
            start_date=self.date2,
            done_date=self.date3)
        k.save()

    def _get_target_class(self):
        from kardboard.models import DailyRecord
        return DailyRecord

    def test_calculate(self):
        klass = self._get_target_class()
        for date in self.dates:
            klass.calculate(date)

        self.assertEqual(len(self.dates), klass.objects.all().count())

    def test_batch_update(self):
        klass = self._get_target_class()
        from kardboard.tasks import queue_daily_record_updates

        queue_daily_record_updates.apply(args=[7, ], throw=True)
        self.assertEqual(7, klass.objects.count())

        # update_daily_records should be idempotent
        queue_daily_record_updates.apply(args=[7, ], throw=True)
        self.assertEqual(7, klass.objects.count())


class KardClassTests(KardboardTestCase):
    def setUp(self):
        super(KardClassTests, self).setUp()
        self.old_config = deepcopy(self.config)

    def tearDown(self):
        self.config = deepcopy(self.old_config)

    def _get_target_class(self):
        return self._get_card_class()

    def _make_one(self, **kwargs):
        return self.make_card(**kwargs)

    def test_default_class(self):
        card = self._make_one()
        self.assertEqual(self.config['DEFAULT_CLASS'], card.service_class)


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

    def test_created_at(self):
        now = datetime.datetime.now()
        k = self._make_one()
        k.save()

        expected = (
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second
        )

        actual = (
            k.created_at.year,
            k.created_at.month,
            k.created_at.day,
            k.created_at.hour,
            k.created_at.minute,
            k.created_at.second,)
        self.assertEqual(expected, actual)

    def test_valid_card(self):
        k = self._make_one()
        k.save()
        self.assert_(k.id)

    def test_state_if_done(self):
        states = self.config.get('CARD_STATES')
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
        klass.objects.all().delete()

        done_date = datetime.date(
            year=2011, month=6, day=15)
        card = self._make_one(done_date=done_date)
        card.save()

        done_date = datetime.date(
            year=2011, month=6, day=17)
        card = self._make_one(done_date=done_date)
        card.save()

        done_date = datetime.date(
            year=2011, month=6, day=30)
        card = self._make_one(done_date=done_date)
        card.save()

        self.assertEqual(3,
            klass.objects.done_in_month(year=2011, month=6, day=30).count())

    def test_moving_cycle_time(self):
        klass = self._get_target_class()
        expected = klass.objects.done().average('_cycle_time')

        expected = int(round(expected))
        actual = klass.objects.moving_cycle_time(
            year=2011, month=6, day=12)
        self.assertEqual(expected, actual)

    def test_moving_lead_time(self):
        klass = self._get_target_class()
        expected = klass.objects.done().average('_lead_time')

        expected = int(round(expected))
        actual = klass.objects.moving_lead_time(
            year=2011, month=6, day=12)
        self.assertEqual(expected, actual)

    def test_done_in_week(self):
        klass = self._get_target_class()
        klass.objects.all().delete()

        done_date = datetime.date(
            year=2011, month=6, day=15)
        card = self._make_one(done_date=done_date)
        card.save()

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

    def test_priority(self):
        klass = self._get_target_class()
        klass.objects.all().delete()

        now = datetime.datetime.now()
        older = now - datetime.timedelta(days=1)
        oldest = now - datetime.timedelta(days=2)
        oldestest = now - datetime.timedelta(days=3)
        oldestester = now - datetime.timedelta(days=4)
        k = self._make_one(key="K-0", priority=1,
            backlog_date=older, start_date=None)
        k1 = self._make_one(key="K-1", priority=2,
            backlog_date=oldest, start_date=None)
        k2 = self._make_one(key="K-2", priority=3,
            backlog_date=oldestest, start_date=None)
        k3 = self._make_one(key="K-3", priority=4,
            backlog_date=oldestester, start_date=None)

        test_cards = [k, k1, k2, k3]
        [c.save() for c in test_cards]

        expected = [
            (k.key, k.priority),
            (k1.key, k1.priority),
            (k2.key, k2.priority),
            (k3.key, k3.priority),
        ]

        actual = [(c.key, c.priority) for c in klass.backlogged()]

        self.assertEqual(expected, actual)

    def test_key_uppercase(self):
        k = self._make_one()
        k.key = "cmscmh-1"
        k.save()

        self.assertEqual("CMSCMH-1", k.key)


class KardWarningTests(KardTests):
    def setUp(self):
        super(KardWarningTests, self).setUp()
        lower = self.wip_card.current_cycle_time() - 1
        upper = self.wip_card.current_cycle_time() + 5
        self.config['CYCLE_TIME_GOAL'] = (lower, upper)

    def test_warning(self):
        self.assertEqual(True, self.wip_card.cycle_in_goal)
        self.assertEqual(False, self.wip_card.cycle_over_goal)


class KardBlockingTests(KardTests):
    def setUp(self):
        super(KardBlockingTests, self).setUp()

    def test_basic_blocking(self):
        # Requires a reason
        self.assertRaises(TypeError,
            self.wip_card.block)

        self.wip_card.block("For British eyes only!")
        self.wip_card.save()

        self.assertEqual(True, self.wip_card.blocked)
        self.assertEqual(True, self.wip_card.blocked_ever)

        self.wip_card.unblock()
        self.assertEqual(False, self.wip_card.blocked)
        self.assertEqual(True, self.wip_card.blocked_ever)

    def test_multiple_blockings(self):
        self.wip_card.block("Did someone say... wonder?!")
        self.wip_card.unblock()
        self.wip_card.save()
        self.assertEqual(1, len(self.wip_card.blockers))
        self.assertEqual(True, self.wip_card.blocked_ever)

        self.wip_card.block("I want the animation rights")
        self.wip_card.unblock()
        self.wip_card.save()
        self.assertEqual(2, len(self.wip_card.blockers))
        self.assertEqual(True, self.wip_card.blocked_ever)

    def test_blocking_and_moving(self):
        """
        A card that is blocked, if it's states move
        should be unblocked with the date
        at which the state edit is made.

        Cards that are blocked, if they're moving state,
        one direction or the other must be unblocked.
        """
        states = self.config.get('CARD_STATES')

        blocked_at = datetime.datetime(2011, 9, 14)
        self.wip_card.block("Annyong", blocked_at)
        self.wip_card.save()

        self.wip_card.state = states[-2]
        self.wip_card.save()

        self.assertEqual(False, self.wip_card.blocked)

        now = datetime.datetime.now()
        blocker = self.wip_card.blockers[0]
        unblocked_at = blocker.unblocked_at
        self.assertEqual(
            [now.year, now.month, now.day],
            [unblocked_at.year, unblocked_at.month, unblocked_at.day]
        )

    def test_blocking_history(self):
        blocked_at = datetime.datetime(2011, 9, 14)
        self.wip_card.block("Annyong", blocked_at)
        self.wip_card.save()

        self.assertEqual(1, len(self.wip_card.blockers))
        blocker = self.wip_card.blockers[0]
        self.assertEqual(blocker.reason, "Annyong")
        self.assertEqual(
            blocker.blocked_at.year,
            blocked_at.year
        )
        self.assertEqual(
            blocker.blocked_at.month,
            blocked_at.month
        )
        self.assertEqual(
            blocker.blocked_at.day,
            blocked_at.day
        )

        unblocked_at = datetime.datetime(2012, 9, 14)
        self.wip_card.unblock(unblocked_at=unblocked_at)
        self.wip_card.save()
        blocker = self.wip_card.blockers[0]
        self.assertEqual(blocker.reason, "Annyong")
        self.assertEqual(
            blocker.unblocked_at.year,
            unblocked_at.year
        )
        self.assertEqual(
            blocker.unblocked_at.month,
            unblocked_at.month
        )
        self.assertEqual(
            blocker.unblocked_at.day,
            unblocked_at.day
        )


class PersonTests(KardboardTestCase):
    def setUp(self):
        super(PersonTests, self).setUp()
        self.cards = [self.make_card() for i in xrange(0, 3)]
        [c.save() for c in self.cards]
        self.person = self._make_one()

    def _get_target_class(self):
        from kardboard.models import Person
        return Person

    def _make_one(self, **kwargs):
        return self.make_person(**kwargs)

    def test_updated_at(self):
        p = self._make_one()
        self.assertEqual(None, p.updated_at)
        p.save()

        p.reload()
        now = datetime.datetime.now()
        updated_at = p.updated_at
        diff = now - updated_at
        self.assert_(diff.seconds <= 1)

    def test_deleted_card(self):
        """
        If a card is placed in any of
        the three lists, and then later
        deleted, it should be removed from the
        list upon Person.save()
        """
        card = self.cards[0]
        card2 = self.cards[1]
        card3 = self.cards[2]

        self.person.report(card)
        self.person.report(card2)

        self.person.develop(card)
        self.person.develop(card3)

        self.person.test(card)
        self.person.save()

        card.delete()
        self.person.reload()
        self.person.cleanup()
        self.person.save()

        self.assertEqual(1, len(self.person.reported))
        self.assertEqual(1, len(self.person.developed))
        self.assertEqual(0, len(self.person.tested))

    def test_doing_more_than_one_thing(self):
        """
            A person should be able to perform
            all roles on a kard: reporter,
            developer, tester.
        """
        card = self.cards[0]
        card2 = self.cards[1]
        card3 = self.cards[2]

        self.person.report(card)
        self.person.report(card2)

        self.person.develop(card)
        self.person.develop(card3)

        self.person.test(card)

        self.assertEqual(2, len(self.person.reported))
        self.assertEqual(2, len(self.person.developed))
        self.assertEqual(1, len(self.person.tested))

    def test_report(self):
        """
            Multiple calls with the same card to a Person's
            report() method should result in only one record
            of them being the reporter on that card.
        """
        card = self.cards[0]
        other_card = self.cards[1]

        self.assertEqual(0, len(self.person.reported))

        self.person.report(card)
        self.assertEqual(1, len(self.person.reported))
        self.person.report(card)
        self.assertEqual(1, len(self.person.reported))

        self.person.report(other_card)
        self.assertEqual(2, len(self.person.reported))

    def test_develop(self):
        """
            Multiple calls with the same card to a Person's
            develop() method should result in only one record
            of them being the developer on that card.
        """
        card = self.cards[0]
        other_card = self.cards[1]

        self.assertEqual(0, len(self.person.developed))

        self.person.develop(card)
        self.assertEqual(1, len(self.person.developed))
        self.person.develop(card)
        self.assertEqual(1, len(self.person.developed))

        self.person.develop(other_card)
        self.assertEqual(2, len(self.person.developed))

    def test_test(self):
        """
            Multiple calls with the same card to a Person's
            test() method should result in only one record
            of them being the developer on that card.
        """
        card = self.cards[0]
        other_card = self.cards[1]

        self.assertEqual(0, len(self.person.tested))

        self.person.test(card)
        self.assertEqual(1, len(self.person.tested))
        self.person.test(card)
        self.assertEqual(1, len(self.person.tested))

        self.person.test(other_card)
        self.assertEqual(2, len(self.person.tested))
