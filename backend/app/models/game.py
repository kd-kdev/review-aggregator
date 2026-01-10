from app.extensions import db


class Game(db.Model):
    __tablename__ = "games"

    appid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    capsule_image_v5 = db.Column("capsule_imagev5", db.String)

    query_summary = db.relationship(
        "QuerySummary", back_populates="game", uselist=False
    )


class QuerySummary(db.Model):
    __tablename__ = "query_summaries"

    appid = db.Column(db.Integer, db.ForeignKey("games.appid"), primary_key=True)
    total_reviews = db.Column(db.Integer)
    total_positive = db.Column(db.Integer)
    total_negative = db.Column(db.Integer)

    game = db.relationship("Game", back_populates="query_summary")
