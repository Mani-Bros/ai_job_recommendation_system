import os
import secrets
from flask import Flask
from .db import init_db
from .auth import auth_bp
from .routes import bp

def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db()
    app.register_blueprint(auth_bp)
    app.register_blueprint(bp)
    return app
