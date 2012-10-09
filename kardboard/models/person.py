import datetime

from kardboard.app import app
from kardboard.models.kard import Kard

class Person(app.db.Document):
    name = app.db.StringField(required=True, unique=True)
    """A unique string that identifies the person"""

    reported = app.db.ListField(
        app.db.ReferenceField('Kard', dbref=False),
        required=False)
    """The list of cards the person was responsible for reporting."""

    developed = app.db.ListField(
        app.db.ReferenceField('Kard', dbref=False),
        required=False)
    """The list of cards the person was responsible for developing."""

    tested = app.db.ListField(
        app.db.ReferenceField('Kard', dbref=False),
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