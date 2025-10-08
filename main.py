from crypt import methods
from urllib import response
import requests
import json
from flask import request, jsonify, render_template
from config import app
from pydantic import BaseModel
from models import QueryMeta


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
    # potentially expand on this to add more options to the query ?
    link = "https://store.steampowered.com/appreviews/" + game_id_string + "?json=1"
    r = requests.get(link).content
    return r


# Testing route for getting Pydantic from JSON
# mapped to button for testing
@app.route("/get_info/<int:game_id>", methods=["GET"])
def get_info(game_id):
    game_id_string = str(game_id)
    # potentially expand on this to add more options to the query ?
    link = "https://store.steampowered.com/appreviews/" + game_id_string + "?json=1"
    response = requests.get(link)  # gets the JSON response from Steam's API

    response_dict = (
        response.json()
    )  # parses the HTTP response body as JSON & returns a python dict

    query_summary = response_dict.get(
        "query_summary"
    )  # extracts the 'query_summary' sub-dict from API response
    parsed = QueryMeta(
        **query_summary
    )  # instanciates the Pydantic model using the 'query_summary' dict, pydantic validates field types & will coerce where appropriate

    return parsed.model_dump_json(indent=2)


# Search endpoint
@app.route("/search?")
def search():
    text = request.form["text"]
    text_str = str(text)

    return text_str


if __name__ == "__main__":
    app.run(debug=True)
