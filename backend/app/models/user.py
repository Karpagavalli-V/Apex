import re
import uuid
from datetime import datetime, timezone
from app.extensions import password_manager

VALID_ROLES = {"customer", "admin"}

class User:
    """User entity representation and serialization helpers."""
    @staticmethod
    def hash_pin(pin: str) -> str:
        """Validates that PIN is exactly 4 numeric digits and returns its bcrypt hash."""
        clean_pin = str(pin).strip()
        if not re.match(r"^\d{4}$", clean_pin):
            raise ValueError("UPI Transaction PIN must be exactly 4 numeric digits.")
        return password_manager.hash_password(clean_pin)

    @staticmethod
    def verify_pin(pin: str, pin_hash: str) -> bool:
        """Verifies a 4-digit numeric PIN against a stored bcrypt hash."""
        if not pin or not pin_hash:
            return False
        clean_pin = str(pin).strip()
        if not re.match(r"^\d{4}$", clean_pin):
            return False
        return password_manager.verify_password(clean_pin, pin_hash)

    @staticmethod
    def create_document(
        email: str,
        username: str,
        plain_password: str,
        full_name: str,
        role: str = "customer",
        is_active: bool = True,
        phone_number: str = "",
        transaction_pin: str = ""
    ) -> dict:
        """
        Creates a new user document for MongoDB storage.
        Always hashes password using bcrypt and assigns unique user_id and apex_pay_id.
        """
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid user role: {role}. Must be one of {VALID_ROLES}")

        now = datetime.now(timezone.utc)
        clean_username = username.strip()
        clean_phone = phone_number.strip()
        pin_hash = User.hash_pin(transaction_pin) if transaction_pin else ""

        return {
            "user_id": f"usr_{uuid.uuid4().hex[:12]}",
            "email": email.strip().lower(),
            "username": clean_username,
            "apex_pay_id": f"{clean_username.lower()}@apex",
            "phone_number": clean_phone,
            "password_hash": password_manager.hash_password(plain_password),
            "transaction_pin_hash": pin_hash,
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
        Never exposes password hashes, PIN hashes, or raw internal MongoDB IDs.
        """
        if not user_doc:
            return {}

        created_at = user_doc.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        updated_at = user_doc.get("updated_at")
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        username = user_doc.get("username", "")
        apex_pay_id = user_doc.get("apex_pay_id") or (f"{username.lower()}@apex" if username else "")
        phone_number = user_doc.get("phone_number", "")
        has_pin = bool(user_doc.get("transaction_pin_hash"))

        return {
            "user_id": user_doc.get("user_id"),
            "email": user_doc.get("email"),
            "username": username,
            "apex_pay_id": apex_pay_id,
            "phone_number": phone_number,
            "has_transaction_pin": has_pin,
            "full_name": user_doc.get("full_name"),
            "role": user_doc.get("role", "customer"),
            "is_active": user_doc.get("is_active", True),
            "created_at": created_at,
            "updated_at": updated_at
        }
