from mongoengine import (
    Document,
    StringField,
    ListField,
    DateTimeField,
)

from kardboard.util import now


class Card(Document):
    """
    Represents a card on a Kanban board.
    """

    key = StringField(required=True, unique=True)
    """A unique string that matches a Kard up to a ticket in a parent system."""

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

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = now()

        super(Card, self).save(*args, **kwargs)
