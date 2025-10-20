from flask import Blueprint, jsonify, render_template
from app.models import Game, QuerySummary
from app.schemas import GameSchema

game_bp = Blueprint("game", __name__)


@game_bp.route("/<int:game_id>", methods=["GET"])
def get_game(game_id):
    game = Game.query.get_or_404(game_id)
    query = QuerySummary.query.get_or_404(game_id)

    game_data = GameSchema.model_validate(game).model_dump()

    filtered_data = {
        "appid": game_data["appid"],
        "name": game_data["name"],
        "developers": game_data["developers"],
        "publishers": game_data["publishers"],
    }

    return render_template("game.html", game=game, query=query)
