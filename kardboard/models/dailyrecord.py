import datetime

from kardboard.app import app
from kardboard.models.kard import Kard
from kardboard.models.reportgroup import ReportGroup
from kardboard.util import make_end_date

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