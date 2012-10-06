from kardboard.app import app


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
