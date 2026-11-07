from flask import Blueprint, request, jsonify, current_app
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from app.extensions import mongo_manager, password_manager, jwt_manager
from app.models.user import User
from app.utils.errors import (
    ValidationError,
    AuthenticationError,
    ConflictError,
    NotFoundError
)
from app.utils.validators import (
    validate_registration_payload,
    validate_login_payload,
    validate_change_password_payload
)
from app.utils.auth_guards import jwt_required, roles_required, get_current_user
from app.utils.logger import logger

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Public customer registration endpoint.
    Strictly forces role='customer' to prevent unauthorized admin creation.
    """
    data = request.get_json(silent=True)
    validated = validate_registration_payload(data)

    db = mongo_manager.get_db()
    if db is None:
        raise AuthenticationError("Database service is currently unavailable.")

    # Check for existing email or username before insert for clearer error messages
    existing_email = db.users.find_one({"email": validated["email"]})
    if existing_email:
        raise ConflictError("An account with this email address already exists.")

    existing_user = db.users.find_one({"username": validated["username"]})
    if existing_user:
        raise ConflictError("An account with this username already exists.")

    # Always enforce role='customer' for public registration
    user_doc = User.create_document(
        email=validated["email"],
        username=validated["username"],
        plain_password=validated["password"],
        full_name=validated["full_name"],
        role="customer",
        phone_number=str(data.get("phone_number") or data.get("phone") or "").strip()
    )

    try:
        db.users.insert_one(user_doc)
        logger.info(f"New customer registered: {user_doc['username']} ({user_doc['user_id']})")
    except DuplicateKeyError as err:
        logger.warning(f"Duplicate registration attempt caught by unique index: {err}")
        raise ConflictError("Email or username is already in use.")

    # Generate JWT token
    token = jwt_manager.generate_token(
        user_id=user_doc["user_id"],
        role=user_doc["role"],
        secret_key=current_app.config["JWT_SECRET_KEY"],
        expires_in=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )

    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "data": {
            "user": User.serialize(user_doc),
            "access_token": token
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticates customer or admin via email/username and password.
    Returns access token and serialized user info.
    """
    data = request.get_json(silent=True)
    validated = validate_login_payload(data)
    identifier = validated["identifier"]
    password = validated["password"]

    db = mongo_manager.get_db()
    if db is None:
        raise AuthenticationError("Database service is currently unavailable.")

    # Query by email (normalized lower) or username
    user = db.users.find_one({
        "$or": [
            {"email": identifier.lower()},
            {"username": identifier}
        ]
    })

    if not user:
        logger.warning(f"Failed login attempt for non-existent identifier: {identifier}")
        raise AuthenticationError("Invalid email/username or password.")

    if not user.get("is_active", True):
        raise AuthenticationError("This account has been deactivated. Please contact support.")

    if not password_manager.verify_password(password, user.get("password_hash", "")):
        logger.warning(f"Failed login attempt (wrong password) for user: {user.get('username')}")
        raise AuthenticationError("Invalid email/username or password.")

    token = jwt_manager.generate_token(
        user_id=user["user_id"],
        role=user.get("role", "customer"),
        secret_key=current_app.config["JWT_SECRET_KEY"],
        expires_in=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )

    logger.info(f"User logged in successfully: {user.get('username')} [{user.get('role')}]")

    return jsonify({
        "success": True,
        "message": "Authentication successful",
        "data": {
            "user": User.serialize(user),
            "access_token": token
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user_profile():
    """Returns the authenticated user's profile."""
    current_user = get_current_user()
    db = mongo_manager.get_db()
    user_doc = db.users.find_one({"user_id": current_user["user_id"]})
    if not user_doc:
        raise NotFoundError("User profile could not be found.")

    return jsonify({
        "success": True,
        "data": {
            "user": User.serialize(user_doc)
        }
    }), 200


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required
def change_password():
    """Updates the authenticated user's password."""
    current_user = get_current_user()
    data = request.get_json(silent=True)
    validated = validate_change_password_payload(data)

    db = mongo_manager.get_db()
    user_doc = db.users.find_one({"user_id": current_user["user_id"]})
    if not user_doc:
        raise NotFoundError("User account not found.")

    if not password_manager.verify_password(validated["old_password"], user_doc.get("password_hash", "")):
        raise AuthenticationError("Current password is incorrect.")

    new_hash = password_manager.hash_password(validated["new_password"])
    now = datetime.now(timezone.utc)

    db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"password_hash": new_hash, "updated_at": now}}
    )

    logger.info(f"Password changed successfully for user: {current_user['username']}")

    return jsonify({
        "success": True,
        "message": "Password updated successfully."
    }), 200


@auth_bp.route("/admin/create-admin", methods=["POST"])
@jwt_required
@roles_required("admin")
def create_admin():
    """
    Admin-only endpoint to securely provision new administrator accounts.
    Cannot be accessed by regular customers or unauthenticated users.
    """
    data = request.get_json(silent=True)
    validated = validate_registration_payload(data)

    db = mongo_manager.get_db()
    if db.users.find_one({"email": validated["email"]}):
        raise ConflictError("An account with this email already exists.")
    if db.users.find_one({"username": validated["username"]}):
        raise ConflictError("An account with this username already exists.")

    admin_doc = User.create_document(
        email=validated["email"],
        username=validated["username"],
        plain_password=validated["password"],
        full_name=validated["full_name"],
        role="admin"
    )

    db.users.insert_one(admin_doc)
    logger.info(f"Admin account created: {admin_doc['username']} by {get_current_user()['username']}")

    return jsonify({
        "success": True,
        "message": "Administrator account created successfully",
        "data": {
            "user": User.serialize(admin_doc)
        }
    }), 201
