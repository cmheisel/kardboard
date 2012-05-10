import datetime
import math
import importlib

from dateutil.relativedelta import relativedelta

from mongoengine.queryset import QuerySet, Q

from kardboard.app import app
from kardboard.util import (
    business_days_between,
    month_range,
    make_end_date,
    make_start_date,
    munge_date,
    week_range,
    now,
    log_exception,
)


class PersonCardSet(object):
    def __init__(self, name):
        super(PersonCardSet, self).__init__()
        self.name = name
        self.cards = set()
        self.defects = set()

    @property
    def all_cards(self):
        return self.cards.union(self.defects)

    def add_card(self, card):
        defect_classes = app.config.get('DEFECT_CLASSES', ())
        if card.service_class in defect_classes:
            self.defects.add(card)
        else:
            self.cards.add(card)

    @property
    def count(self):
        return len(self.cards)

    @property
    def sorted_cards(self):
        cards = list(self.cards)
        cards.sort(key=lambda c: c.done_date, reverse=True)
        return cards

    @property
    def sorted_defects(self):
        defects = list(self.defects)
        defects.sort(key=lambda c: c.done_date, reverse=True)
        return defects

    @property
    def cycle_time(self):
        times = [c.cycle_time for c in self.all_cards]
        return int(round(float(sum(times)) / len(times)))

    def __cmp__(self, other):
        return cmp(self.count, other.count)


class DisplayBoard(object):
    def __init__(self, teams=None, done_days=7):
        self.states = States()
        self.done_days = done_days
        self._cards = None

        if teams == None:
            teams = [t for t in app.config['CARD_TEAMS'] if t]  # Remove blanks
        self.teams = teams

    def __iter__(self):
        for row in self.rows:
            yield row

    @property
    def headers(self):
        headers = [dict(state=s) for s in self.states]
        if len(self.teams) > 1:
            headers.insert(0, dict(label='Team'))

        header_counts = [0 for h in headers]
        for row in self.rows:
            for cell in row:
                index = row.index(cell)
                if cell.get('cards', None) != None:
                    header_counts[index] += len(cell['cards'])
                else:
                    header_counts[index] = None

        for i in xrange(0, len(header_counts)):
            count = header_counts[i]
            headers[i]['count'] = count

        return tuple(headers)

    @property
    def rows(self):
        rows = []
        for team in self.teams:
            row = []
            if len(self.teams) > 1:
                row.append({'label': team})
            for state in self.states:
                cards = [card for card in self.cards if card.state == state and card.team == team]
                if state in self.states.pre_start:
                    pri_cards = [c for c in cards if c.priority != None]
                    pri_cards = sorted(pri_cards, key=lambda c: c.priority)
                    versioned = [c for c in cards if c.priority == None and c._version != None]
                    versioned.sort(key=lambda c: c._version)
                    non_versioned = [c for c in cards if c.priority == None and c._version == None]

                    cards = pri_cards + versioned + non_versioned
                elif state in self.states.in_progress:
                    cards = sorted(cards, key=lambda c: c.current_cycle_time())
                    cards.reverse()
                else:
                    try:
                        cards = sorted(cards, key=lambda c: c.done_date)
                    except TypeError, e:
                        bad_cards = [c for c in cards if not c.done_date]
                        message = "The following cards have no done date: %s" % (bad_cards)
                        log_exception(e, message)
                        raise
                cell = {'cards': cards, 'state': state}
                row.append(cell)
            rows.append(row)
        return rows

    @property
    def cards(self):
        if self._cards:
            return self._cards

        in_progress_q = Q(done_date=None,
            start_date__exists=True,
            team__in=self.teams)
        backlog_q = Q(backlog_date__exists=True,
            start_date=None,
            team__in=self.teams)
        done_q = Q(done_date__gte=now() - relativedelta(days=self.done_days),
            team__in=self.teams)
        cards_query = backlog_q | in_progress_q | done_q

        self._cards = list(Kard.objects.filter(cards_query))
        return self._cards


class ReportGroup(object):
    def __init__(self, group, queryset):
        self.group = group
        self.qs = queryset
        super(ReportGroup, self).__init__()

    @property
    def queryset(self):
        groups_config = app.config.get('REPORT_GROUPS', {})
        group = groups_config.get(self.group, ())
        query = Q()

        if group:
            teams = group[0]
            for team in teams:
                query = Q(team=team) | query

        if query:
            return self.qs.filter(query)
        return self.qs


class States(object):
    def __init__(self, config=None):
        if not config:
            config = app.config
        self.config = config
        self.states = config.get('CARD_STATES', ())
        self.backlog = self._find_backlog()
        self.start = self._find_start()
        self.done = self._find_done()
        self.pre_start = self._find_pre_start()
        self.in_progress = self._find_in_progress()

    def _find_pre_start(self):
        """
        Find all states, in order, that come
        before a start_date is applied.
        """
        return [s for s in self.states if self.states.index(s) < self.states.index(self.start)]

    def _find_in_progress(self):
        """
        Find all states, in order, that come after after backlog
        but before done.
        """
        pre_done = [s for s in self.states if self.states.index(s) < self.states.index(self.done)]
        last_state_before_start = self.pre_start[-1]
        in_progress = [s for s in pre_done if self.states.index(s) > self.states.index(last_state_before_start)]
        return in_progress

    def _find_done(self):
        default = -1
        done = self.config.get('DONE_STATE', default)
        return self.states[done]

    def _find_start(self):
        default = 1
        start = self.config.get('START_STATE', default)
        return self.states[start]

    def _find_backlog(self):
        default = 0
        backlog = self.config.get('BACKLOG_STATE', default)
        return self.states[backlog]

    def __iter__(self):
        for state in self.states:
            yield state

    def __unicode__(self):
        return unicode(self.states)

    def __str__(self):
        return str(self.states)

    def index(self, *args, **kwargs):
        return self.states.index(*args, **kwargs)

    @property
    def for_forms(self):
        form_list = [('', ''), ]  # Add a blank
        form_list.extend([(state, state) for state in self.states])
        return tuple(form_list)


class KardQuerySet(QuerySet):
    def done_in_week(self, year=None, month=None, day=None, date=None):
        """
        Kards that were completed in the week of the specified day.
        """
        if not date:
            date = munge_date(year, month, day)
            date = make_end_date(date=date)
        start_date, end_date = week_range(date)

        results = self.done().filter(done_date__lte=date,
            done_date__gte=start_date)
        return results

    def average(self, field_str):
        count = self.count()
        the_sum = sum([getattr(k, field_str) for k in self.filter().only(field_str)])

        if count == 0:
            return float('nan')

        return the_sum / float(count)

    def moving_cycle_time(self, year=None, month=None, day=None, weeks=4):
        """
        The moving average of cycle time for every day in the last N weeks.
        """

        end_date = make_end_date(year, month, day)
        start_date = end_date - relativedelta(weeks=weeks)
        start_date = make_start_date(date=start_date)

        qs = self.done().filter(
            done_date__lte=end_date,
            done_date__gte=start_date,
            )

        average = qs.average('_cycle_time')
        if math.isnan(average):
            average = 0

        return int(round(average))

    def moving_lead_time(self, year=None, month=None, day=None, weeks=4):
        """
        The moving average of lead time for every day in the last N weeks.
        """

        end_date = make_end_date(year, month, day)
        start_date = end_date - relativedelta(weeks=weeks)
        start_date = make_start_date(date=start_date)

        qs = self.done().filter(
            done_date__lte=end_date,
            done_date__gte=start_date,
            )

        average = qs.average('_lead_time')
        if math.isnan(average):
            average = 0

        return int(round(average))

    def done(self):
        """
        Kards that have been completed.
        """
        return self.filter(done_date__exists=True)

    def done_in_month(self, year=None, month=None, day=None, date=None):
        """
        Kards that have been completed in the specified month.
        """
        if not date:
            date = munge_date(year=year, month=month, day=day)
            date = make_end_date(date=date)

        start_date, faux_end_date = month_range(date)

        results = self.done().filter(done_date__lte=date,
            done_date__gte=start_date)
        return results


class Person(app.db.Document):
    name = app.db.StringField(required=True, unique=True)
    """A unique string that identifies the person"""

    reported = app.db.ListField(
        app.db.ReferenceField('Kard'),
        required=False)
    """The list of cards the person was responsible for reporting."""

    developed = app.db.ListField(
        app.db.ReferenceField('Kard'),
        required=False)
    """The list of cards the person was responsible for developing."""

    tested = app.db.ListField(
        app.db.ReferenceField('Kard'),
        required=False)
    """The list of cards the person was responsible for testing."""

    updated_at = app.db.DateTimeField(required=True)

    def report(self, kard):
        if kard not in self.reported:
            self.reported.append(kard)

    def develop(self, kard):
        if kard not in self.developed:
            self.developed.append(kard)

    def test(self, kard):
        if kard not in self.tested:
            self.tested.append(kard)

    def _is_card(self, kandidate):
        if isinstance(kandidate, Kard):
            return True
        return False

    def in_progress(self, kardlist):
        kards = [k for k in kardlist if self._is_card(k)]
        wip = [k for k in kards if not k.done_date]
        wip.sort(key=lambda r: r.current_cycle_time())
        wip.reverse()
        return wip

    def is_done(self, kardlist):
        kards = [k for k in kardlist if self._is_card(k)]
        kards = [k for k in kards if k.done_date]
        kards.sort(key=lambda r: r.done_date)
        kards.reverse()
        return kards

    def cleanup(self):
        [self.reported.remove(k) for k in list(self.reported) if not isinstance(k, Kard)]
        [self.developed.remove(k) for k in list(self.developed) if not isinstance(k, Kard)]
        [self.tested.remove(k) for k in list(self.tested) if not isinstance(k, Kard)]

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        self.cleanup()
        super(Person, self).save(*args, **kwargs)


class BlockerRecord(app.db.EmbeddedDocument):
    """
    Represents a blockage of work for a card.
    """

    reason = app.db.StringField(required=True)
    """The reason why the card was considered blocked."""

    blocked_at = app.db.DateTimeField(required=True)
    """When the card's blockage started."""

    unblocked_at = app.db.DateTimeField(required=False)
    """When the card's blockage stopped."""


class Kard(app.db.Document):
    """
    Represents a card on a Kanban board.
    """
    _ticket_system = None

    key = app.db.StringField(required=True, unique=True)
    """A unique string that matches a Kard up to a ticket in a parent system."""

    title = app.db.StringField()
    backlog_date = app.db.DateTimeField(required=True)
    """When the card entered the backlog."""

    start_date = app.db.DateTimeField()
    """When the card was started."""

    done_date = app.db.DateTimeField()
    """When the card was completed."""

    _cycle_time = app.db.IntField(db_field="cycle_time")
    _lead_time = app.db.IntField(db_field="lead_time")
    team = app.db.StringField(required=True, default="")
    """A selection from a user supplied list of teams/assignees. See :ref:`CARD_TEAMS`"""

    state = app.db.StringField(required=True, default="Unknown")
    """Which column on the kanban board the card is in."""
    priority = app.db.IntField(required=False)
    """Used when ordering cards in the backlog."""

    blocked = app.db.BooleanField(default=False)
    """Is the card currently blocked."""

    blocked_ever = app.db.BooleanField(default=False)
    """Was the card ever blocked in its history."""

    blockers = app.db.ListField(
        app.db.EmbeddedDocumentField(BlockerRecord),
    )

    created_at = app.db.DateTimeField(required=True)

    _service_class = app.db.StringField(required=True, db_field="service_class")
    _version = app.db.StringField(required=False, db_field="version")

    _ticket_system_updated_at = app.db.DateTimeField()
    _ticket_system_data = app.db.DictField()

    meta = {
        'queryset_class': KardQuerySet,
        'collection': 'kard',
        'ordering': ['+priority', '-backlog_date']
    }

    EXPORT_FIELDNAMES = (
        'key',
        'title',
        'backlog_date',
        'start_date',
        'done_date',
        'state',
    )

    def _convert_dates_to_datetimes(self, date):
        if not date:
            return None
        if not hasattr(date, "hour"):
            return datetime.datetime(date.year, date.month, date.day,
                23, 59, 59, 0)
        return date

    def block(self, reason, blocked_at=None):
        if not blocked_at:
            blocked_at = datetime.datetime.now()

        b = BlockerRecord(
            reason=reason,
            blocked_at=blocked_at
        )
        self.blockers.append(b)

        self.blocked = True
        self.blocked_ever = True
        return True

    def unblock(self, unblocked_at=None):
        if not unblocked_at:
            unblocked_at = datetime.datetime.now()
        self.blocked = False

        open_blockers = [b for b in self.blockers if b.unblocked_at == None]
        for b in open_blockers:
            b.unblocked_at = unblocked_at

        return True

    def save(self, *args, **kwargs):
        self.backlog_date = self._convert_dates_to_datetimes(self.backlog_date)
        self.start_date = self._convert_dates_to_datetimes(self.start_date)
        self.done_date = self._convert_dates_to_datetimes(self.done_date)

        if not self.created_at:
            self.created_at = now()

        # Auto move to done
        if self.done_date:
            states = States()
            self.in_progress = False
            self.state = states.done

        # Auto fill in final cycle and lead time
        if self.done_date and self.start_date:
            self._cycle_time = self.cycle_time
            self._lead_time = self.lead_time

        # If a card is blocked, inspect it's previous state and
        # if we're moving states unblock it
        if self.blocked:
            try:
                k = Kard.objects.only('state').get(key=self.key, )
                if k.state != self.state:
                    # Card is blocked and it's state is about to change
                    self.unblock()
            except Kard.DoesNotExist:
                #Card isn't saved can't find its previous state
                pass

        self._service_class = self.service_class
        self._version = self.ticket_system.get_version()
        self.key = self.key.upper()

        super(Kard, self).save(*args, **kwargs)

    @property
    def service_class(self):
        # Fill in the service_class from the ticket helper if
        # there is one, and if not the config'd default
        if self.ticket_system.service_class:
            service_class = self.ticket_system.service_class
        else:
            service_class = app.config['DEFAULT_CLASS']
        return service_class.strip()

    @classmethod
    def in_progress(klass, date=None):
        """
        Cards that are in progress as of the supplied date (or now).

        In progress is a semi-tricky calculation.
        If the date is today, it's easy, it's any
        ticket that doesn't have a done_date.
        If the date is earlier, then it's:

            a.) Any ticket without a done_date
            whose backlog_date is lte
            than the reference date **AND**

            b.) Any ticket with a done_date
            greater than the reference date
            and a start_date earlier than
            the reference date
        """
        if not date:
            return klass.objects.filter(done_date=None,
                start_date__exists=True)

        query_a = Q(done_date=None) & Q(start_date__lte=date)
        query_b = Q(done_date__gt=date) & Q(start_date__lte=date)

        results_a = list(klass.objects.filter(query_a))
        results_b = list(klass.objects.filter(query_b))

        all_ids = [c.id for c in results_a]
        all_ids = set(all_ids)
        all_ids.update([c.id for c in results_b])
        qs = klass.objects.filter(id__in=all_ids)
        return qs

    @classmethod
    def backlogged(klass, date=None):
        """
        Cards that are backlogged as of the supplied date (or now).

        Backlogged is a semi-tricky calculation.
        If the date is today, it's easy, it's any
        ticket that doesn't have a done_date or a
        start_date.

        If the date is earlier, then it's:
            a.) Any ticket without a done_date
                whose backlog_date is lte
                than the reference date and who's
                start_date is lte the reference date **AND**

            b.) Any ticket with a start_date
                greater than the reference date
                and a backlog_date earlier than
                the reference date
        """
        if not date:
            return klass.objects.filter(start_date=None)

        query_a = Q(start_date=None) & \
            Q(backlog_date__lte=date)
        query_b = Q(start_date__gt=date) & \
            Q(backlog_date__lte=date)

        results_a = list(klass.objects.filter(query_a))
        results_b = list(klass.objects.filter(query_b))

        all_ids = [c.id for c in results_a]
        all_ids = set(all_ids)
        all_ids.update([c.id for c in results_b])
        return klass.objects.filter(id__in=all_ids)

    @property
    def cycle_time(self):
        """
        Caclucation of the number of days between the start of a card
        and its completion. Returns None if the card hasn't completed yet.
        """
        if self.start_date and self.done_date:
            return business_days_between(self.start_date, self.done_date)

    @property
    def lead_time(self):
        """
        Caclucation of the number of days between the backlogging of a card
        and its completion. Returns None if the card hasn't completed yet.
        """
        if self.done_date:
            return business_days_between(self.backlog_date, self.done_date)

    def current_cycle_time(self, today=None):
        """
        Caclucation of the number of days between the start of a card
        and a comparison point (defaults to today).
        Returns None if the card hasn't started yet.
        """
        if not self.start_date:
            return None

        if not today:
            today = datetime.datetime.now()
        return business_days_between(self.start_date, today)

    @property
    def cycle_goal(self):
        goal_range = app.config.get('CYCLE_TIME_GOAL', ())
        try:
            lower, upper = goal_range
        except ValueError:
            return None
        return lower, upper

    @property
    def cycle_in_goal(self):
        if self.cycle_vs_goal == 0:
            return True
        return False

    @property
    def cycle_over_goal(self):
        if self.cycle_vs_goal > 0:
            return True
        return False

    @property
    def cycle_vs_goal(self):
        if not self.cycle_goal:
            return 0

        lower, upper = self.cycle_goal
        super_upper = upper * 2
        if self.done_date:
            current = self.cycle_time
        else:
            current = self.current_cycle_time()

        if current < lower:
            return -1
        elif current >= lower and current <= upper:
            return 0
        elif current >= super_upper:
            return 2
        elif current >= upper:
            return 1

    def __unicode__(self):
        backlog, start, done = self.backlog_date, self.start_date, \
            self.done_date
        priority = ""

        if backlog:
            backlog = backlog.strftime("%m/%d/%Y")
        if start:
            start = start.strftime("%m/%d/%Y")
        if done:
            done = done.strftime("%m/%d/%Y")
        if hasattr(self, 'priority') and self.priority:
            priority = "P%s | " % (self.priority, )

        return u"%s -- %s%s | %s | %s" % (self.key, priority, backlog, start, done)

    @property
    def ticket_system(self):
        """
        Instance of :ref:`TICKET_HELPER`
        """

        if self._ticket_system:
            return self._ticket_system

        helper_setting = app.config['TICKET_HELPER']
        modname = '.'.join(helper_setting.split('.')[:-1])
        klassnam = helper_setting.split('.')[-1]
        mod = importlib.import_module(modname)
        klass = getattr(mod, klassnam)

        helper = klass(app.config, self)
        self._ticket_system = helper
        return helper

    @property
    def ticket_system_data(self):
        """
        Dictionary of data supplied by :ref:`TICKET_HELPER`.

        The exact composition of the dictionary varies by the helper used.
        """
        if not self._ticket_system_data:
            return {}
        else:
            return self._ticket_system_data


class FlowReport(app.db.Document):
    """
    Represents a daily snapshot of cards by state, per team.
    """

    date = app.db.DateTimeField(required=True, unique=False, unique_with=['group', ])
    """The date for the records"""

    group = app.db.StringField(required=True, default="all", unique_with=['date', ])
    """The report group to which this daily report belongs."""

    data = app.db.ListField(app.db.DictField(),)
    """The snapshot of data provided for that team on the date."""

    updated_at = app.db.DateTimeField(required=True)
    """The datetime the record was last updated at."""

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        super(FlowReport, self).save(*args, **kwargs)

    def __str__(self):
        return "<FlowReport: %s -- %s>" % (self.group, self.date)

    @property
    def snapshot(self):
        try:
            from collections import OrderedDict
        except ImportError:
            from ordereddict import OrderedDict
        snapshot = OrderedDict()
        for state in self.data:
            snapshot[state['name']] = state
        return snapshot


    @classmethod
    def capture(klass, group='all'):
        date = datetime.datetime.now()
        date = make_end_date(date=date)
        try:
            r = klass.objects.get(date=date, group=group)
        except klass.DoesNotExist:
            r = klass()
            r.date = date
            r.group = group

        states = States()

        for state in states:
            group_cards = ReportGroup(group, Kard.objects.filter(state=state)).queryset
            state_data = {
                'name': state,
                'count': group_cards.count()
            }
            r.data.append(state_data)

        r.save()
        return r

class DailyRecord(app.db.Document):
    """
    Represents a daily record of kard activity.
    """

    date = app.db.DateTimeField(required=True, unique=False, unique_with=['group', ])
    """The date for the records"""

    backlog = app.db.IntField(required=True)
    """The number of cards in planning on the record's date."""

    in_progress = app.db.IntField(required=True)
    """The number of cards in doing on the record's date."""

    done = app.db.IntField(required=True)
    """The number of cards done on or before the record's date."""

    completed = app.db.IntField(required=True)
    """The number of cards that were completed on that date."""

    moving_cycle_time = app.db.IntField(required=True)
    """The moving average cycle time for that date."""

    moving_lead_time = app.db.IntField(required=True)
    """The moving average lead time for that date."""

    updated_at = app.db.DateTimeField(required=True)
    """The datetime the record was last updated at."""

    group = app.db.StringField(required=True, default="all", unique_with=['date', ])
    """The report group to which this daily report belongs."""

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        super(DailyRecord, self).save(*args, **kwargs)

    @property
    def backlog_cum(self):
        """Total number of cards in backlog, in_progress and done."""
        return self.backlog + self.in_progress + self.done

    @property
    def in_progress_cum(self):
        """Total number of cards in in_progress and done."""
        return self.in_progress + self.done

    @classmethod
    def calculate(klass, date, group='all'):
        """
        Creates or updates a DailyRecord for the date provided.
        """

        date = make_end_date(date=date)

        try:
            k = klass.objects.get(date=date, group=group)
        except klass.DoesNotExist:
            k = klass()
            k.date = date
            k.group = group

        k.backlog = ReportGroup(group, Kard.backlogged(date)).queryset.count()
        k.in_progress = ReportGroup(group, Kard.in_progress(date)).queryset.count()
        k.done = ReportGroup(group, Kard.objects.filter(done_date__lte=date)).queryset.count()
        k.completed = ReportGroup(group, Kard.objects.filter(done_date=date)).queryset.count()
        k.moving_cycle_time = ReportGroup(group, Kard.objects).queryset.moving_cycle_time(
            year=date.year, month=date.month, day=date.day)
        k.moving_lead_time = ReportGroup(group, Kard.objects).queryset.moving_lead_time(
            year=date.year, month=date.month, day=date.day)

        k.save()
