from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    IntField,
    BooleanField,
    ValidationError,
)

from kardboard.util import now, delta_in_hours


class StateLog(Document):
    card = StringField(required=True)
    """The card this record is for."""
    state = StringField(required=True)
    """The state the card was in for this record"""
    entered_at = DateTimeField(required=True)
    """Datetime the card entered its state"""
    exited_at = DateTimeField(required=False)
    """Datetime the card exited this state"""
    blocked = BooleanField(default=False)
    """Was this card ever blocked for the duration of this state record."""
    message = StringField(required=False)
    """A note about the state."""

    _blocked_at = DateTimeField(required=False)
    _unblocked_at = DateTimeField(required=False)
    _blocked_duration = IntField(required=False)
    _duration = IntField(required=False)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    meta = {
        'cascade': False,
        'ordering': ['-created_at'],
        'indexes': ['card', 'state', ['card', 'created_at']]
    }

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created_at = now()

        if not self.entered_at:
            self.entered_at = now()

        if self.exited_at and self.exited_at < self.entered_at:
            raise ValidationError("A card may not exit before it enters")

        if self.entered_at and self.exited_at:
            self._duration = self.duration
        self.updated_at = now()
        super(StateLog, self).save(*args, **kwargs)

    def __repr__(self):
        return "<StateLog: %s, %s, %s -- %s, %s hours>" % (
            self.card,
            self.state,
            self.entered,
            self.exited,
            self._duration)

    @property
    def duration(self):
        if self._duration is not None:
            return self._duration

        if self.exited_at is not None:
            exited_at = self.exited_at
        else:
            exited_at = now()
        delta = exited_at - self.entered_at
        return delta_in_hours(delta)

    @property
    def as_dict(self):
        return {
            'card': self.card,
            'state': self.state,
            'entered_at': self.entered_at,
            'exited_at': self.exited_at,
            'blocked': self.blocked,
            'message': self.message,
        }

    @property
    def blocker(self):
        return {
            'card': self.card,
            'state': self.state,
            'blocked': self.blocked,
            'blocked_at': self._blocked_at,
            'unblocked_at': self._unblocked_at,
            'duration': self.block_duration,
            'message': self.message,
        }

    @property
    def block_duration(self):
        if self._blocked_at is None:
            return 0

        if self._blocked_duration is not None:
            return self._blocked_duration

        if self._unblocked_at is not None:
            unblocked_at = self._unblocked_at
        else:
            unblocked_at = now()
        delta = unblocked_at - self._blocked_at
        return delta_in_hours(delta)

    def block(self, message, blocked_at=None):
        if blocked_at is None:
            blocked_at = now()
        self.message = message
        self._blocked_at = blocked_at
        self.blocked = True
        self.save()

    def unblock(self, unblocked_at=None):
        if unblocked_at is None:
            unblocked_at = now()
        self._unblocked_at = unblocked_at
        self._blocked_duration = self.block_duration
        self.blocked = False
        self.save()
