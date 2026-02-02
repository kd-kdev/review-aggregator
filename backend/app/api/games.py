from flask import Blueprint, jsonify, abort, request
from app.extensions import db
from app.models.game import Game, QuerySummary
from app.schemas.game import GameDetailResponseSchema, GameOverviewResponse
from sqlalchemy import func
from app.models.review import Review
from app.schemas.review import (
    ReviewSchema,
    ReviewKeywordSummarySchema,
    ReviewKeywordResponseSchema,
)

games_bp = Blueprint("games", __name__, url_prefix="/api/games")


# Home page route -> gets overview of games + their review stats
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


# Game page route - stub for now
@games_bp.get("/<int:appid>")
def get_game(appid: int):
    game = db.session.query(Game).filter(Game.appid == appid).first()

    if not game:
        abort(404, description="Game not found")

    summary = db.session.query(QuerySummary).filter(QuerySummary.appid == appid).first()

    return jsonify(
        GameDetailResponseSchema(
            appid=game.appid,
            name=game.name,
            capsule_image_v5=game.capsule_image_v5,
            release_date=game.release_date,
            review_score_desc=summary.review_score_desc if summary else None,
            total_reviews=summary.total_reviews if summary else 0,
            total_positive=summary.total_positive if summary else 0,
            total_negative=summary.total_negative if summary else 0,
        ).model_dump()
    )


# keyword search functionality route:
@games_bp.get("/<int:appid>/reviews/keyword")
def keyword_reviews(appid: int):
    keyword = request.args.get("keyword", "").strip()
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    if len(keyword) < 2:
        abort(400, description="Keyword too short")

    # Base filtered query
    base_query = db.session.query(Review).filter(
        Review.appid == appid,
        Review.review.ilike(f"%{keyword}%"),
    )

    # Fetch paginated reviews
    reviews = (
        base_query.order_by(Review.timestamp_created.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Count total number of reviews containing keyword
    reviews_with_keyword = base_query.count()

    # Calculate total keyword occurrences
    occurrences = (
        db.session.query(
            func.sum(
                (
                    func.length(func.lower(Review.review))
                    - func.length(
                        func.replace(func.lower(Review.review), keyword.lower(), "")
                    )
                )
                / func.nullif(func.length(keyword), 0)
            )
        )
        .filter(
            Review.appid == appid,
            Review.review.ilike(f"%{keyword}%"),
        )
        .scalar()
    ) or 0

    # Build Pydantic models
    review_models = [
        ReviewSchema.model_validate(r, from_attributes=True) for r in reviews
    ]

    summary_model = ReviewKeywordSummarySchema(
        keyword=keyword,
        reviews_with_keyword=reviews_with_keyword,
        occurrences=int(occurrences),
    )

    response_model = ReviewKeywordResponseSchema(
        keyword=keyword,
        summary=summary_model,
        reviews=review_models,
    )

    return jsonify(
        {
            **response_model.model_dump(),
            "has_more": offset + len(reviews) < reviews_with_keyword,
        }
    )
