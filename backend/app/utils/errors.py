from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.utils.logger import logger

class AppError(Exception):
    """Base application exception."""
    status_code = 500
    error_code = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str, details=None, status_code=None, error_code=None):
        super().__init__(message)
        self.message = message
        self.details = details or []
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code

    def to_dict(self):
        payload = {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
            }
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


class ValidationError(AppError):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class AuthenticationError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class AuthorizationError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"


class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


def register_error_handlers(app):
    """Registers centralized JSON error handlers on the Flask app."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        logger.warning(f"Handled application error: {err.error_code} - {err.message}")
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        logger.warning(f"HTTP exception: {err.code} - {err.description}")
        return jsonify({
            "success": False,
            "error": {
                "code": getattr(err, "name", "HTTP_ERROR").upper().replace(" ", "_"),
                "message": err.description
            }
        }), err.code

    @app.errorhandler(Exception)
    def handle_unhandled_exception(err):
        logger.exception(f"Unhandled server exception: {str(err)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred."
            }
        }), 500
