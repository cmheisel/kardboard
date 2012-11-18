from mongoengine import (
    Document,
    StringField,
    ListField,
    DateTimeField,
    SortedListField,
    ReferenceField,
    PULL,
)

from kardboard.util import now
from kardboard.models.statelog import StateLog


class Card(Document):
    """
    Represents a card on a Kanban board.
    """

    key = StringField(required=True, unique=True, primary_key=True)
    """A unique string that matches a Card to a ticket in a parent system."""

    title = StringField(required=True)
    """A human friendly headline for the card"""

    teams = ListField(StringField(), required=True)
    """A selection from a user supplied list of teams"""

    service_class = StringField(required=True, default="Standard")
    """The service class of the card"""

    due_date = DateTimeField(required=False)
    """The date by when a card most be done."""

    issue_type = StringField(required=False)
    """The type of card it is, Defect, Improvement, etc."""

    created_at = DateTimeField(required=True)
    """The datetime the card was created in the system."""

    state_logs = SortedListField(ReferenceField(StateLog,
        reverse_delete_rule=PULL))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = now()
            if len(self.state_logs) == 0:
                self.set_state(card=self.key, state='Backlog',
                    entered_at=self.created_at)

        super(Card, self).save(*args, **kwargs)

    @property
    def state_log(self):
        # TODO: Implement this as a lazy list
        return [sl.as_dict for sl in self.state_logs]

    @property
    def current_state(self):
        sl = self.state_log[0]
        return sl

    def set_state(self, state, **kwargs):
        """Sets the current state for the card."""
        from kardboard.models.statelog import StateLog
        sl, created = StateLog.objects.get_or_create(card=self.key,
            state=state)
        for attr, value in kwargs.items():
            setattr(sl, attr, value)
        sl.save()
        if sl not in self.state_logs:
            if len(self.state_logs) > 0:
                previous_sl = self.state_logs[-1]
                previous_sl.exited_at = sl.entered_at
                previous_sl.save()
            self.state_logs.append(sl)

    def block(self, message, blocked_at=None):
        """Blocks the card in its current state."""
        sl = self.state_logs[0]
        sl.block(message, blocked_at)

    def unblock(self, unblocked_at=None):
        """Unblocks the card in its current state."""
        sl = self.state_logs[0]
        sl.unblock(unblocked_at)

    @property
    def blocker(self):
        sl = self.state_logs[0]
        return sl.blocker

    @property
    def blocked(self):
        sl = self.state_logs[0]
        return sl.blocker['blocked']
