from functools import wraps
from flask import request, g, current_app
from app.extensions import jwt_manager, mongo_manager
from app.utils.errors import AuthenticationError, AuthorizationError
from app.utils.logger import logger

def jwt_required(f):
    """
    Decorator to protect routes requiring a valid JWT access token.
    Extracts Bearer token, decodes payload, and attaches g.current_user.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            raise AuthenticationError("Authorization header is missing")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationError("Authorization header must be formatted as 'Bearer <token>'")

        token = parts[1]
        secret = current_app.config["JWT_SECRET_KEY"]
        payload = jwt_manager.decode_token(token, secret)

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Malformed token payload")

        db = mongo_manager.get_db()
        if db is None:
            raise AuthenticationError("Database unavailable during authentication")

        user = db.users.find_one({"user_id": user_id})
        if not user:
            raise AuthenticationError("User associated with this token no longer exists")

        if not user.get("is_active", True):
            raise AuthenticationError("User account is inactive or suspended")

        # Attach sanitized user info to request context
        g.current_user = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role", "customer"),
            "is_active": user.get("is_active", True)
        }
        return f(*args, **kwargs)

    return decorated_function


def roles_required(*allowed_roles):
    """
    Decorator to restrict access to users having one of the specified roles.
    Must be used AFTER @jwt_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(g, "current_user", None)
            if not current_user:
                raise AuthenticationError("Authentication required before authorization check")

            user_role = current_user.get("role")
            if user_role not in allowed_roles:
                logger.warning(
                    f"Access denied for user {current_user.get('username')} "
                    f"with role '{user_role}'. Required roles: {allowed_roles}"
                )
                raise AuthorizationError(
                    f"Access forbidden: requires one of the following roles: {', '.join(allowed_roles)}"
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user() -> dict:
    """Helper to retrieve current user from context."""
    return getattr(g, "current_user", None)
