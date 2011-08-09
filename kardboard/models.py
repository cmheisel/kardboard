import datetime
import math
import importlib

from dateutil.relativedelta import relativedelta

from mongoengine.queryset import QuerySet, Q

from kardboard import app
from kardboard.util import (
    business_days_between,
    slugify,
    month_range,
    make_end_date,
    make_start_date,
    munge_date,
    week_range,
)


class Board(app.db.Document):
    name = app.db.StringField(required=True, unique=True)
    categories = app.db.ListField(app.db.StringField())
    cards = app.db.ListField(app.db.EmbeddedDocumentField('Kard'))
    slug = app.db.StringField(required=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Board, self).save(*args, **kwargs)


class KardQuerySet(QuerySet):
    def done_in_week(self, year=None, month=None, day=None):
        """
        Kards that were completed in the week of the specified day.
        """

        date = munge_date(year, month, day)
        start_date, end_date = week_range(date)

        results = self.done().filter(done_date__lte=date,
            done_date__gte=start_date)
        return results

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

    def done_in_month(self, year=None, month=None, day=None):
        """
        Kards that have been completed in the specified month.
        """

        date = munge_date(year=year, month=month, day=day)

        start_date, faux_end_date = month_range(date)

        results = self.done().filter(done_date__lte=date,
            done_date__gte=start_date)
        return results


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

    state = app.db.StringField(required=True, default="Unknown")
    """Which column on the kanban board the card is in."""
    priority = app.db.IntField(required=False)
    """Used when ordering cards in the backlog."""

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
