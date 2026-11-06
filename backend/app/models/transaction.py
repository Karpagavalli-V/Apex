import uuid
from datetime import datetime, timezone

VALID_TRANSACTION_TYPES = {"DEPOSIT", "WITHDRAWAL", "TRANSFER"}
VALID_TRANSACTION_STATUSES = {"COMPLETED", "FAILED", "FLAGGED_SUSPICIOUS", "FLAGGED_HIGH_RISK"}

class Transaction:
    """Transaction ledger domain entity representing immutable financial records."""

    @staticmethod
    def create_document(
        account_id: str,
        user_id: str,
        tx_type: str,
        amount_paise: int,
        balance_after_paise: int,
        status: str = "COMPLETED",
        description: str = "",
        counterparty_account_id: str = None,
        idempotency_key: str = None,
        metadata: dict = None,
        risk_level: str = "NORMAL",
        fraud_probability: float = 0.0
    ) -> dict:
        """
        Creates an immutable ledger transaction document.
        Amounts and balances are strictly stored as integer paise.
        """
        if tx_type.upper() not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type '{tx_type}'. Must be one of {VALID_TRANSACTION_TYPES}")

        if not isinstance(amount_paise, int) or amount_paise <= 0:
            raise ValueError("Transaction amount must be a strictly positive integer amount in paise.")

        if not isinstance(balance_after_paise, int) or balance_after_paise < 0:
            raise ValueError("Resulting balance must be a non-negative integer amount in paise.")

        now = datetime.now(timezone.utc)
        return {
            "transaction_id": f"tx_{uuid.uuid4().hex[:14]}",
            "account_id": account_id,
            "user_id": user_id,
            "type": tx_type.upper(),
            "amount_paise": amount_paise,
            "balance_after_paise": balance_after_paise,
            "status": status,
            "risk_level": risk_level,
            "fraud_probability": round(float(fraud_probability), 4),
            "description": description.strip() if description else "",
            "counterparty_account_id": counterparty_account_id,
            "idempotency_key": idempotency_key,
            "timestamp": now,
            "metadata": metadata or {}
        }

    @staticmethod
    def serialize(tx_doc: dict) -> dict:
        """Serializes transaction document for JSON API output."""
        if not tx_doc:
            return {}

        amount_paise = int(tx_doc.get("amount_paise", 0))
        amount_inr = round(amount_paise / 100.0, 2)
        balance_after_paise = int(tx_doc.get("balance_after_paise", 0))
        balance_after_inr = round(balance_after_paise / 100.0, 2)

        timestamp = tx_doc.get("timestamp")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()

        return {
            "transaction_id": tx_doc.get("transaction_id"),
            "account_id": tx_doc.get("account_id"),
            "user_id": tx_doc.get("user_id"),
            "type": tx_doc.get("type"),
            "amount_paise": amount_paise,
            "amount_inr": amount_inr,
            "balance_after_paise": balance_after_paise,
            "balance_after_inr": balance_after_inr,
            "currency": "INR",
            "status": tx_doc.get("status", "COMPLETED"),
            "risk_level": tx_doc.get("risk_level", "NORMAL"),
            "fraud_probability": tx_doc.get("fraud_probability", 0.0),
            "description": tx_doc.get("description", ""),
            "counterparty_account_id": tx_doc.get("counterparty_account_id"),
            "timestamp": timestamp,
            "metadata": tx_doc.get("metadata", {})
        }
