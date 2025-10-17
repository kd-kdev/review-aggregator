from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from datetime import date, datetime
from app import db


class Game(db.Model):
    __tablename__ = "games"

    appid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    capsule_imagev5 = db.Column(db.String(255))
    developers = db.Column(db.String(255))
    publishers = db.Column(db.String(255))
    platforms = db.Column(db.String(100))
    release_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime(timezone=True))

    query_summary = db.relationship(
        "QuerySummary",  # the related model
        back_populates="game",  # used on the other model for bidirectional access
        uselist=False,  # single object, not a list
    )
    reviews = db.relationship(
        "Review",  # the related model
        back_populates="game",
        cascade="all, delete-orphan",  # optional: delete reviews if game is deleted
    )


class QuerySummary(db.Model):
    __tablename__ = "query_summaries"

    appid = db.Column(
        db.Integer,
        db.ForeignKey("games.appid"),
        primary_key=True,
    )
    num_reviews = db.Column(db.Integer)
    review_score = db.Column(db.Integer)
    review_score_desc = db.Column(db.Text)
    total_positive = db.Column(db.Integer)
    total_negative = db.Column(db.Integer)
    total_reviews = db.Column(db.Integer)
    cursor = db.Column(db.Text)
    updated_at = db.Column(db.DateTime(timezone=True))
    raw_json = db.Column(JSONB)

    game = db.relationship("Game", back_populates="query_summary")


class Review(db.Model):
    __tablename__ = "reviews"

    recommendationid = db.Column(db.BigInteger, primary_key=True)
    appid = db.Column(db.BigInteger, db.ForeignKey("games.appid"))
    steamid = db.Column(db.BigInteger)
    language = db.Column(db.Text)
    review = db.Column(db.Text)
    voted_up = db.Column(db.Boolean)
    votes_up = db.Column(db.Integer)
    votes_funny = db.Column(db.Integer)
    timestamp_created = db.Column(db.DateTime(timezone=True))
    timestamp_updated = db.Column(db.DateTime(timezone=True))
    steam_purchase = db.Column(db.Boolean)
    received_for_free = db.Column(db.Boolean)
    written_during_early_access = db.Column(db.Boolean)
    primarily_steam_deck = db.Column(db.Boolean)
    raw_json = db.Column(JSONB)

    game = db.relationship("Game", back_populates="reviews")
