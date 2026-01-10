from flask import Blueprint, jsonify
from app.extensions import db
from app.models.game import Game, QuerySummary
from app.schemas.game import GameOverviewResponse

games_bp = Blueprint("games", __name__)


@games_bp.route("/overview", methods=["GET"])
def games_overview():
    rows = (
        db.session.query(
            Game.appid.label("appid"),
            Game.name.label("name"),
            Game.capsule_image_v5.label("capsule"),
            QuerySummary.total_reviews.label("total_reviews"),
            QuerySummary.total_positive.label("positive"),
            QuerySummary.total_negative.label("negative"),
        )
        .outerjoin(QuerySummary, QuerySummary.appid == Game.appid)
        .order_by(QuerySummary.total_reviews.desc().nullslast())
        .limit(50)
        .all()
    )

    data = []

    for r in rows:
        total = r.total_reviews or 0
        pos = r.positive or 0
        neg = r.negative or 0

        data.append(
            {
                "appid": r.appid,
                "name": r.name,
                "capsule_image": r.capsule,
                "total_reviews": total,
                "positive_pct": round((pos / total) * 100, 2) if total else 0.0,
                "negative_pct": round((neg / total) * 100, 2) if total else 0.0,
            }
        )

    response = GameOverviewResponse(data=data, count=len(data))
    return jsonify(response.model_dump())
