from flask import Blueprint, jsonify

games_bp = Blueprint("games", __name__)


@games_bp.route("/", methods=["GET"])
def list_games():
    return jsonify({"message": "list games"})


@games_bp.route("/<int:appid>", methods=["GET"])
def get_game(appid):
    return jsonify({"appid": appid})
