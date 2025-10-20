from flask import Blueprint, jsonify, render_template
from app.models import Game, QuerySummary
from app.schemas import GameSchema
from flask_restx import Namespace, Resource, fields

game_bp = Blueprint("game", __name__)

# Docs for swagger
game_ns = Namespace("game", description="Game operations")

game_model = game_ns.model(
    "Game",
    {
        "appid": fields.Integer(),
        "name": fields.String(),
        "developers": fields.String(),
        "publishers": fields.String(),
        "platforms": fields.String(),
        "release_date": fields.String(),
    },
)


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
