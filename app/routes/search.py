from flask import Blueprint, request, jsonify
from app.models import Game
from app.schemas import GameSchema

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
def search():
    text = request.args.get("g", None)

    games = Game.query.filter(Game.name.ilike(f"%{text}%")).all()
    results = [GameSchema.model_validate(game).model_dump() for game in games]

    return jsonify(results)
