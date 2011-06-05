import datetime
import math

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
        date = munge_date(year, month, day)
        start_date, end_date = week_range(date)

        results = self.done().filter(done_date__lte=end_date,
            done_date__gte=start_date)
        return results

    def moving_cycle_time(self, year=None, month=None, day=None, weeks=4):
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

    def done(self):
        return self.filter(done_date__exists=True)

    def done_in_month(self, year=None, month=None):
        date = munge_date(year=year, month=month)

        start_date, end_date = month_range(date)

        results = self.done().filter(done_date__lte=end_date,
            done_date__gte=start_date)
        return results

class Kard(app.db.Document):
    """
    Represents a card on a Kanban board.

    key = JIRA or other ticket tracker unique ID
    title = short human friendly name for the card

    backlog_date = date the card entered the backlog
    start_date = date at which the card was considered in progress
    done_date = date the card was considered done
    """

    key = app.db.StringField(required=True, unique=True)
    title = app.db.StringField()
    backlog_date = app.db.DateTimeField(required=True)
    start_date = app.db.DateTimeField()
    done_date = app.db.DateTimeField()
    _cycle_time = app.db.IntField(db_field="cycle_time")
    _lead_time = app.db.IntField(db_field="lead_time")
    category = app.db.StringField(required=True, default="Uncategorized")

    meta = {
        'queryset_class': KardQuerySet,
    }

    def save(self, *args, **kwargs):
        if self.done_date:
            self.in_progress = False

        if self.done_date and self.start_date:
            self._cycle_time = self.cycle_time
            self._lead_time = self.lead_time

        super(Kard, self).save(*args, **kwargs)

    @classmethod
    def in_progress(klass, date=None):
        """
        In progress is a semi-tricky calculation.
        If the date is today, it's easy, it's any
        ticket that doesn't have a done_date.
        If the date is earlier, then it's:
            a.) Any ticket without a done_date
                whose backlog_date is lte
                than the reference date
            -AND-
            b.) Any ticket with a done_date
                greater than the reference date
                and a start_date earlier than
                the reference date
        """
        if not date:
            return klass.objects.filter(done_date=None)

        query_a = Q(done_date=None) & Q(backlog_date__lte=date)
        query_b = Q(done_date__gt=date) & Q(backlog_date__lte=date)

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
