from mongoengine import signals

from kardboard.app import app
from kardboard.util import now, delta_in_hours
from kardboard.models.kard import Kard


class StateLog(app.db.Document):
    card = app.db.ReferenceField(
        'Kard',
        reverse_delete_rule=app.db.CASCADE,
        required=True,
        dbref=False,
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
    service_class = app.db.StringField(required=False)
    # The service class the card was in while in this state

    created_at = app.db.DateTimeField(required=True)
    updated_at = app.db.DateTimeField(required=True)

    meta = {
        'cascade': False,
        'ordering': ['-created_at'],
        'indexes': ['card', 'state', ['card', 'created_at']]
    }

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created_at = now()
        if self.entered and self.exited:
            self._duration = self.duration
        self.updated_at = now()
        super(StateLog, self).save(*args, **kwargs)

    def __repr__(self):
        return "<StateLog: %s, %s, %s -- %s, %s hours>" % (
            self.card.key,
            self.state,
            self.entered,
            self.exited,
            self._duration
        )

    @classmethod
    def kard_pre_save(cls, sender, document, **kwargs):
        observed_card = document

        if observed_card.state_changing is False:
            # No need to worry about logging it, nothing's changing!
            return None

        try:
            observed_card.old_state
        except AttributeError:
            raise

        # If you're here it's because the observed_card's state is changing
        if observed_card.old_state is not None:
            try:
                slo = cls.objects.get(
                        card=observed_card,
                        state=observed_card.old_state,
                        service_class=observed_card.service_class.get('name'))
                slo.exited = now()
                slo.save() # Close the old state log
            except cls.DoesNotExist:
                #  For some reason we didn't record the old state, this should only happen when first rolled out
                pass

    @classmethod
    def kard_post_save(cls, sender, document, **kwargs):
        observed_card = document

        try:
            # This could be a freshly created card, so create a log for it
            sl, created = cls.objects.get_or_create(auto_save=False,
                card=observed_card,
                state=observed_card.state)
            if created:
                sl.entered = now()
        except cls.MultipleObjectsReturned:
            sl = cls.objects.filter(
                card=observed_card,
                state=observed_card.state)[0]

        sl.service_class=observed_card.service_class.get('name')
        sl.save()

    @property
    def duration(self):
        if self._duration is not None:
            return self._duration

        if self.exited is not None:
            exited = self.exited
        else:
            exited = now()
        delta = exited - self.entered
        return delta_in_hours(delta)

signals.pre_save.connect(StateLog.kard_pre_save, sender=Kard)
signals.post_save.connect(StateLog.kard_post_save, sender=Kard)
