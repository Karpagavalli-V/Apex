import uuid
from datetime import datetime, timezone
from app.extensions import password_manager

VALID_ROLES = {"customer", "admin"}

class User:
    """User entity representation and serialization helpers."""
    @staticmethod
    def create_document(
        email: str,
        username: str,
        plain_password: str,
        full_name: str,
        role: str = "customer",
        is_active: bool = True
    ) -> dict:
        """
        Creates a new user document for MongoDB storage.
        Always hashes password using bcrypt and assigns unique user_id.
        """
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid user role: {role}. Must be one of {VALID_ROLES}")

        now = datetime.now(timezone.utc)
        return {
            "user_id": f"usr_{uuid.uuid4().hex[:12]}",
            "email": email.strip().lower(),
            "username": username.strip(),
            "password_hash": password_manager.hash_password(plain_password),
            "full_name": full_name.strip(),
            "role": role,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now
        }

    @staticmethod
    def serialize(user_doc: dict) -> dict:
        """
        Sanitizes a MongoDB user document for API output.
        Never exposes password hashes or raw internal MongoDB IDs.
        """
        if not user_doc:
            return {}

        created_at = user_doc.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        updated_at = user_doc.get("updated_at")
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        return {
            "user_id": user_doc.get("user_id"),
            "email": user_doc.get("email"),
            "username": user_doc.get("username"),
            "full_name": user_doc.get("full_name"),
            "role": user_doc.get("role", "customer"),
            "is_active": user_doc.get("is_active", True),
            "created_at": created_at,
            "updated_at": updated_at
        }
