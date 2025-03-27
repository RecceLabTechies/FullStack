import os
from flask import Flask
from flask_cors import CORS
from app.utils.logging_config import setup_logging
from app.database.connection import Database
from app.routes.user_routes import user_bp
from app.routes.data_routes import data_bp
from app.config import MAX_CONTENT_LENGTH, CORS_CONFIG

logger = setup_logging()


def create_app():
    """Create and configure Flask application"""
    # Initialize Flask application
    app = Flask(__name__)

    # Configure CORS
    CORS(
        app,
        resources={r"/*": CORS_CONFIG},
    )

    # Increase maximum content length to allow larger file uploads
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # Initialize database connection
    Database.initialize()

    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(data_bp)

    return app
