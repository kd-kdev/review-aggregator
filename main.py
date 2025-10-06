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


if __name__ == "__main__":
    app.run(debug=True)
