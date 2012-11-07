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

    key = StringField(required=True, unique=True)
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

    state_log = SortedListField(ReferenceField(StateLog,
        reverse_delete_rule=PULL))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = now()
            if len(self.state_log) == 0:
                self.set_state(card=self.key, state='Backlog',
                    entered_at=self.created_at)

        super(Card, self).save(*args, **kwargs)

    @property
    def current_state(self):
        sl = self.state_log[0]
        return sl.as_dict

    def set_state(self, state, **kwargs):
        from .statelog import StateLog
        sl, created = StateLog.objects.get_or_create(card=self.key,
            state=state)
        for attr, value in kwargs.items():
            setattr(sl, attr, value)
        sl.save()
        if sl not in self.state_log:
            self.state_log.append(sl)
