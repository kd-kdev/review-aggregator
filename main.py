from crypt import methods
from urllib import response
import requests
from flask import request, jsonify, render_template
from config import app


@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/get_game", methods=["GET"])
def get_gameReviews():
    r = requests.get(
        "https://store.steampowered.com/appreviews/292000?json=1&filter=recent"
    ).content
    return r


# Search functionality
@app.route("/search_game/<int:game_id>", methods=["GET"])
def search_game(game_id):
    game_id_string = str(game_id)
    link = "https://store.steampowered.com/appreviews/" + game_id_string + "?json=1"
    r = requests.get(link).content
    return r


if __name__ == "__main__":
    app.run(debug=True)
