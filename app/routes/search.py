from flask import Blueprint, render_template, request, jsonify
from app.models import Game
from app.schemas import GameSchema

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
def search_page():
    return render_template("search.html")


@search_bp.route("/results", methods=["GET"])
def search():
    text = request.args.get("g", None)

    games = Game.query.filter(Game.name.ilike(f"%{text}%")).all()
    results = [GameSchema.model_validate(g).model_dump() for g in games]

    return jsonify(results)
