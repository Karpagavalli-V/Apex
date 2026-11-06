import os
from flask import Flask, request
from flask_cors import CORS
from app.config import config_by_name
from app.extensions import mongo_manager
from app.utils.errors import register_error_handlers
from app.utils.logger import logger
from app.routes.auth import auth_bp
from app.routes.system import system_bp
from app.routes.accounts import accounts_bp
from app.routes.transactions import transactions_bp
from app.routes.ml import ml_bp
from app.routes.ai import ai_bp

def create_app(config_name: str = None) -> Flask:
    """
    Application factory for the AI-Enhanced Banking API.
    Initializes configuration, extensions, blueprints, and error handlers.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True
    )

    # Initialize MongoDB extension & ensure indexes
    mongo_manager.init_app(app)

    # Register centralized error handlers
    register_error_handlers(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(ai_bp)


    @app.before_request
    def log_request_info():
        # Do not log raw passwords from auth endpoints
        logger.debug(f"Incoming {request.method} request to {request.path}")

    @app.after_request
    def apply_security_headers(response):
        """Apply defensive HTTP security headers to protect against common web vulnerabilities."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    logger.info(f"Flask Banking App initialized in '{config_name}' environment.")
    return app
