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
)


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

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
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
    category = app.db.StringField(required=True, default="Uncategorized")
    """A user-supplied taxonomy for cards. See :ref:`CARD_CATEGORIES`"""
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
        'category',
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

        if self.done_date:
            self.in_progress = False
            self.state = app.config.get("CARD_STATES", [])[-1]

        if self.done_date and self.start_date:
            self._cycle_time = self.cycle_time
            self._lead_time = self.lead_time

        if self.blocked:
            try:
                k = Kard.objects.only('state').get(key=self.key, )
                if k.state != self.state:
                    # Card is blocked and it's state is about to change
                    self.unblock()
            except Kard.DoesNotExist:
                #Card isn't saved can't find its previous state
                pass

        self.key = self.key.upper()

        super(Kard, self).save(*args, **kwargs)

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
        if self.cycle_goal:
            lower, upper = self.cycle_goal
            if self.done_date:
                current = self.cycle_time
            else:
                current = self.current_cycle_time()
            if current >= lower and current <= upper:
                return True
        return False

    @property
    def cycle_over_goal(self):
        if self.cycle_goal:
            lower, upper = self.cycle_goal
            if self.done_date:
                current = self.cycle_time
            else:
                current = self.current_cycle_time()
            if current > upper:
                return True
        return False

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


class DailyRecord(app.db.Document):
    """
    Represents a daily record of kard activity.
    """

    date = app.db.DateTimeField(required=True, unique=True)
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

    meta = {
        'indexes': ['date', ]
    }

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
    def calculate(klass, date):
        """
        Creates or updates a DailyRecord for the date provided.
        """

        date = make_end_date(date=date)

        try:
            k = klass.objects.get(date=date)
        except klass.DoesNotExist:
            k = klass()
            k.date = date

        k.backlog = Kard.backlogged(date).count()
        k.in_progress = Kard.in_progress(date).count()
        k.done = Kard.objects.filter(done_date__lte=date).count()
        k.completed = Kard.objects.filter(done_date=date).count()
        k.moving_cycle_time = Kard.objects.moving_cycle_time(
            year=date.year, month=date.month, day=date.day)
        k.moving_lead_time = Kard.objects.moving_lead_time(
            year=date.year, month=date.month, day=date.day)

        k.save()
