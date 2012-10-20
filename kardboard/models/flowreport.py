import datetime

from kardboard.app import app
from kardboard.models.states import States
from kardboard.models.reportgroup import ReportGroup
from kardboard.models.kard import Kard
from kardboard.util import (
    make_end_date,
)

class FlowReport(app.db.Document):
    """
    Represents a daily snapshot of cards by state, per team.
    """

    date = app.db.DateTimeField(required=True, unique=False, unique_with=['group', ])
    """The date for the records"""

    group = app.db.StringField(required=True, default="all", unique_with=['date', ])
    """The report group to which this daily report belongs."""

    state_counts = app.db.DictField()
    """Kanban state as the key and the count of cards and defects in that state, on this date, for this group."""

    state_card_counts = app.db.DictField()
    """Kanban state as the key and the count of cards in that state, on this date, for this group."""

    updated_at = app.db.DateTimeField(required=True)
    """The datetime the record was last updated at."""

    meta = {
        'indexes': ['date', ('date', 'group')],
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        super(FlowReport, self).save(*args, **kwargs)

    def __str__(self):
        return "<FlowReport: %s -- %s>" % (self.group, self.date)

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
            r.state_counts[state] = group_cards.count()

            non_defects = [c for c in group_cards.only('_type') if c.is_card]
            r.state_card_counts[state] = len(non_defects)

        r.save()
        return r
