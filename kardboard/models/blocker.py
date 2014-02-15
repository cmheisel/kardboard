from kardboard.app import app
from kardboard.util import now, delta_in_hours


class BlockerRecord(app.db.EmbeddedDocument):
    """
    Represents a blockage of work for a card.
    """

    reason = app.db.StringField(required=True)
    """The reason why the card was considered blocked."""

    blocked_at = app.db.DateTimeField(required=True)
    """When the card's blockage started."""

    unblocked_at = app.db.DateTimeField(required=False)
    """When the card's blockage stopped."""

    @property
    def duration(self):
        if self.unblocked_at is not None:
            unblocked_at = self.unblocked_at
        else:
            unblocked_at = now()
        delta = unblocked_at - self.blocked_at
        return delta_in_hours(delta)
