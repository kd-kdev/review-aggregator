from app.extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    recommendationid = db.Column(db.BigInteger, primary_key=True)

    # Relations
    appid = db.Column(
        db.BigInteger,
        db.ForeignKey("games.appid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    steamid = db.Column(db.BigInteger, index=True)

    # Review content
    language = db.Column(db.Text, index=True)
    review = db.Column(db.Text, nullable=False)

    # Votes / sentiment
    voted_up = db.Column(db.Boolean, nullable=False)
    votes_up = db.Column(db.Integer, default=0)
    votes_funny = db.Column(db.Integer, default=0)

    # Timestamps
    timestamp_created = db.Column(db.DateTime(timezone=True), index=True)
    timestamp_updated = db.Column(db.DateTime(timezone=True))

    # Flags
    steam_purchase = db.Column(db.Boolean)
    received_for_free = db.Column(db.Boolean)
    written_during_early_access = db.Column(db.Boolean)
    primarily_steam_deck = db.Column(db.Boolean)

    # Raw payload
    raw_json = db.Column(db.JSON)

    # --- Relationships ---
    game = db.relationship("Game", backref=db.backref("reviews", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Review {self.recommendationid} appid={self.appid}>"
