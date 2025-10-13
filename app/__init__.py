from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, static_folder="../static", template_folder="../templates")

    load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devkey")

    db.init_app(app)
    CORS(app)

    from app.routes.main import main_bp
    from app.routes.search import search_bp
    from app.routes.game import game_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(game_bp, url_prefix="/game")

    return app
