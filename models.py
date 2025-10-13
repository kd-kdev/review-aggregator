from pydantic import BaseModel
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Game(db.Model):
    __tablename__ = "games"

    appid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    capsule_imagev5 = db.Column(db.String(255))
    developers = db.Column(db.String(255))
    publishers = db.Column(db.String(255))
    platforms = db.Column(db.String(100))
    release_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime)
