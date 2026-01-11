from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.extensions import db, migrate
from app.api.health import health_bp
from app.api.games import games_bp
from app.api.search import search_bp


def create_app():
    # Load environment variables
    load_dotenv()

    app = Flask(__name__)

    # -------------------
    # Configuration
    # -------------------
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # -------------------
    # Extensions
    # -------------------
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # -------------------
    # Blueprints (API)
    # -------------------
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(games_bp, url_prefix="/api/games")
    app.register_blueprint(search_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
