import datetime

from kardboard import app
from kardboard.util import business_days_between


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

    def save(self, *args, **kwargs):
        if self.done_date and self.start_date:
            self._cycle_time = self.cycle_time
            self._lead_time = self.lead_time

        super(Kard, self).save(*args, **kwargs)

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
            today = datetime.datetime.today()
        return business_days_between(self.start_date, today)
