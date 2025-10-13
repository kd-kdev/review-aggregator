from flask import Blueprint, jsonify
from app.models import Game
from app.schemas import GameSchema

game_bp = Blueprint("game", __name__)


@game_bp.route("/<int:game_id>", methods=["GET"])
def get_game(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify(GameSchema.model_validate(game).model_dump())
