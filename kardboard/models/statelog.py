from kardboard.app import app
from kardboard.util import now


class StateLog(app.db.Document):
    card = app.db.ReferenceField(
        'Kard',
        reverse_delete_rule=app.db.CASCADE,
        required=True
    )
    # Card that this record is about
    state = app.db.StringField(required=True)
    # The state the card was in for this record
    entered = app.db.DateTimeField(required=True)
    # Datetime the card entered its state
    exited = app.db.DateTimeField(required=False)
    # Datetime the card exited this state
    _duration = app.db.IntField(required=False)
    # The duration the card was in this state

    @property
    def duration(self):
        if self._duration is not None:
            return self._duration

        if self.exited is not None:
            exited = self.exited
        else:
            exited = now()
        delta = exited - self.entered
        hours = (delta.total_seconds() / 60.0) / 60.0
        hours = round(hours)

        return hours

    def save(self, *args, **kwargs):
        if self.entered and self.exited:
            self._duration = self.duration

        super(StateLog, self).save(*args, **kwargs)
