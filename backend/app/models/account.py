import uuid
import random
from datetime import datetime, timezone

VALID_ACCOUNT_TYPES = {"SAVINGS", "CHECKING"}
VALID_ACCOUNT_STATUSES = {"ACTIVE", "FROZEN", "CLOSED"}

class Account:
    """Account domain entity representing customer bank accounts."""

    @staticmethod
    def generate_account_number() -> str:
        """Generates a standard 12-digit account number starting with 100."""
        random_suffix = random.randint(100000000, 999999999)
        return f"100{random_suffix}"

    @staticmethod
    def create_document(
        user_id: str,
        account_type: str = "SAVINGS",
        initial_deposit_paise: int = 0
    ) -> dict:
        """
        Creates a new account document.
        Amounts are strictly stored as integer paise.
        """
        if account_type.upper() not in VALID_ACCOUNT_TYPES:
            raise ValueError(f"Invalid account type '{account_type}'. Must be one of {VALID_ACCOUNT_TYPES}")

        if not isinstance(initial_deposit_paise, int) or initial_deposit_paise < 0:
            raise ValueError("Initial deposit must be a non-negative integer amount in paise.")

        now = datetime.now(timezone.utc)
        return {
            "account_id": f"acc_{uuid.uuid4().hex[:12]}",
            "account_number": Account.generate_account_number(),
            "user_id": user_id,
            "account_type": account_type.upper(),
            "balance_paise": initial_deposit_paise,
            "currency": "INR",
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now
        }

    @staticmethod
    def serialize(account_doc: dict) -> dict:
        """Serializes account document for JSON API output."""
        if not account_doc:
            return {}

        balance_paise = int(account_doc.get("balance_paise", 0))
        balance_inr = round(balance_paise / 100.0, 2)

        created_at = account_doc.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        updated_at = account_doc.get("updated_at")
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        return {
            "account_id": account_doc.get("account_id"),
            "account_number": account_doc.get("account_number"),
            "user_id": account_doc.get("user_id"),
            "account_type": account_doc.get("account_type"),
            "balance_paise": balance_paise,
            "balance_inr": balance_inr,
            "currency": account_doc.get("currency", "INR"),
            "status": account_doc.get("status", "ACTIVE"),
            "created_at": created_at,
            "updated_at": updated_at
        }
