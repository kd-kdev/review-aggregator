from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.extensions import db
from app.schemas.game import GameOverviewResponse

search_bp = Blueprint("search", __name__, url_prefix="/api/games")


@search_bp.get("/search")
def search_games():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"data": [], "count": 0})

    ilike_q = f"%{q}%"

    limit = min(int(request.args.get("limit", 20)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    sql = text("""
        SELECT
          appid,
          name,
          capsule_imagev5 AS capsule_image,
          COALESCE(qs.total_reviews, 0) AS total_reviews,
          COALESCE(qs.total_positive, 0) AS total_positive,
          COALESCE(qs.total_negative, 0) AS total_negative,
          ts_rank_cd(search_tsv, plainto_tsquery('english', :q)) AS rank
        FROM games g
        LEFT JOIN query_summaries qs USING (appid)
        WHERE search_tsv @@ plainto_tsquery('english', :q)
        ORDER BY rank DESC, total_reviews DESC
        LIMIT :limit OFFSET :offset
    """)

    fallback_sql = text("""
        SELECT
          appid,
          name,
          capsule_imagev5 AS capsule_image,
          COALESCE(qs.total_reviews, 0) AS total_reviews,
          COALESCE(qs.total_positive, 0) AS total_positive,
          COALESCE(qs.total_negative, 0) AS total_negative,
          0 AS rank
        FROM games g
        LEFT JOIN query_summaries qs USING (appid)
        WHERE g.name ILIKE :ilike_q
        ORDER BY total_reviews DESC
        LIMIT :limit OFFSET :offset
    """)

    params = {"q": q, "limit": limit, "offset": offset}
    result = db.session.execute(sql, params).all()

    if not result:
        result = db.session.execute(
            fallback_sql,
            {"ilike_q": ilike_q, "limit": limit, "offset": offset},
        ).all()

    rows = []
    for r in result:
        total = r.total_reviews or 0
        pos = r.total_positive or 0
        neg = r.total_negative or 0

        rows.append(
            {
                "appid": r.appid,
                "name": r.name,
                "capsule_image": r.capsule_image,
                "total_reviews": total,
                "positive_pct": round((pos / total) * 100, 2) if total else 0.0,
                "negative_pct": round((neg / total) * 100, 2) if total else 0.0,
            }
        )

    response = GameOverviewResponse(data=rows, count=len(rows))
    return jsonify(response.model_dump())
