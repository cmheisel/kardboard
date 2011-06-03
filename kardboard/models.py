import datetime

from kardboard import app
from kardboard.util import business_days_between


class Kard(app.db.Document):
    key = app.db.StringField(required=True, unique=True, primary_key=True)
    title = app.db.StringField()
    backlog_date = app.db.DateTimeField(required=True)
    start_date = app.db.DateTimeField()
    done_date = app.db.DateTimeField()
    _cycle_time = app.db.IntField(db_field="cycle_time")
    _lead_time = app.db.IntField(db_field="lead_time")

    def save(self, *args, **kwargs):
        if self.done_date and self.start_date:
            self._cycle_time = self.cycle_time
            self._lead_time = self.lead_time

        super(Kard, self).save(*args, **kwargs)

    @property
    def cycle_time(self):
        if self.start_date and self.done_date:
            return business_days_between(self.start_date, self.done_date)

    @property
    def lead_time(self):
        if self.done_date:
            return business_days_between(self.backlog_date, self.done_date)

    def current_cycle_time(self, today=None):
        if not self.start_date:
            return None

        if not today:
            today = datetime.datetime.today()
        return business_days_between(self.start_date, today)
