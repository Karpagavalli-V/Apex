from datetime import datetime, timezone
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from app.extensions import mongo_manager
from app.models.account import Account
from app.models.transaction import Transaction
from app.utils.errors import (
    NotFoundError,
    ValidationError,
    AuthorizationError,
    ConflictError
)
from app.utils.logger import logger

class BankingService:
    """
    Core banking engine providing atomic balance updates, strict overdraft
    safeguards, idempotency caching, and transaction ledger auditing.
    """

    @staticmethod
    def _execute_in_session(callback, max_retries: int = 25):
        """
        Executes callback inside a MongoDB multi-document ACID transaction if
        supported by the cluster; automatically retries on TransientTransactionError
        (such as concurrent WriteConflict) with exponential backoff and jitter.
        """
        client = mongo_manager.client
        if mongo_manager.supports_transactions and client is not None:
            import time
            import random
            for attempt in range(max_retries):
                with client.start_session() as session:
                    try:
                        with session.start_transaction():
                            return callback(session)
                    except PyMongoError as err:
                        is_transient = (
                            err.has_error_label("TransientTransactionError") 
                            or getattr(err, "code", None) == 112
                            or "WriteConflict" in str(err)
                        )
                        if is_transient and attempt < max_retries - 1:
                            delay = 0.01 * (attempt + 1) + random.uniform(0.01, 0.05)
                            time.sleep(delay)
                            continue
                        raise
        else:
            return callback(None)

    @classmethod
    def record_audit(
        cls,
        action: str,
        user_id: str,
        account_id: str = None,
        status: str = "SUCCESS",
        details: dict = None,
        session=None
    ):
        """Records an immutable security and financial audit event."""
        db = mongo_manager.get_db()
        if db is None:
            return

        now = datetime.now(timezone.utc)
        audit_doc = {
            "action": action,
            "user_id": user_id,
            "account_id": account_id,
            "status": status,
            "details": details or {},
            "timestamp": now
        }
        try:
            db.audit_logs.insert_one(audit_doc, session=session)
        except Exception as err:
            logger.error(f"Failed to write audit log: {err}")

    @classmethod
    def check_idempotency(cls, idempotency_key: str, user_id: str, action: str):
        """
        Checks whether a request with the given idempotency key was previously processed.
        Returns the cached response data if found.
        """
        if not idempotency_key:
            return None

        db = mongo_manager.get_db()
        cached = db.idempotency_keys.find_one({
            "key": idempotency_key,
            "user_id": user_id,
            "action": action
        })
        if cached:
            logger.info(f"Idempotent request matched for key: {idempotency_key} [Action: {action}]")
            return cached.get("response")
        return None

    @classmethod
    def save_idempotency(cls, idempotency_key: str, user_id: str, action: str, response: dict, session=None):
        """Caches the successful response payload for an idempotency key."""
        if not idempotency_key:
            return

        db = mongo_manager.get_db()
        now = datetime.now(timezone.utc)
        doc = {
            "key": idempotency_key,
            "user_id": user_id,
            "action": action,
            "response": response,
            "created_at": now
        }
        try:
            db.idempotency_keys.insert_one(doc, session=session)
        except Exception as err:
            logger.warning(f"Failed to record idempotency key (may already exist): {err}")

    @classmethod
    def create_account(
        cls,
        user_id: str,
        account_type: str = "SAVINGS",
        initial_deposit_paise: int = 0,
        idempotency_key: str = None
    ) -> dict:
        """Provisions a new bank account for a customer."""
        cached = cls.check_idempotency(idempotency_key, user_id, "create_account")
        if cached:
            return cached

        db = mongo_manager.get_db()
        user = db.users.find_one({"user_id": user_id})
        if not user:
            raise NotFoundError("User not found")

        def _action(session):
            account_doc = Account.create_document(
                user_id=user_id,
                account_type=account_type,
                initial_deposit_paise=initial_deposit_paise
            )
            db.accounts.insert_one(account_doc, session=session)

            if initial_deposit_paise > 0:
                tx_doc = Transaction.create_document(
                    account_id=account_doc["account_id"],
                    user_id=user_id,
                    tx_type="DEPOSIT",
                    amount_paise=initial_deposit_paise,
                    balance_after_paise=initial_deposit_paise,
                    status="COMPLETED",
                    description="Initial opening deposit"
                )
                db.transactions.insert_one(tx_doc, session=session)

            cls.record_audit(
                action="ACCOUNT_CREATED",
                user_id=user_id,
                account_id=account_doc["account_id"],
                details={"account_type": account_type, "initial_deposit_paise": initial_deposit_paise},
                session=session
            )

            result = {
                "account": Account.serialize(account_doc)
            }
            cls.save_idempotency(idempotency_key, user_id, "create_account", result, session=session)
            return result

        result = cls._execute_in_session(_action)
        logger.info(f"Account {result['account']['account_number']} created for user {user_id}")
        return result

    @classmethod
    def get_user_accounts(cls, user_id: str) -> list:
        """Retrieves all accounts owned by a specific customer."""
        db = mongo_manager.get_db()
        cursor = db.accounts.find({"user_id": user_id}).sort("created_at", -1)
        return [Account.serialize(doc) for doc in cursor]

    @classmethod
    def get_all_accounts(cls, page: int = 1, limit: int = 20) -> dict:
        """Retrieves paginated accounts across all customers (admin only)."""
        db = mongo_manager.get_db()
        skip = (page - 1) * limit
        total = db.accounts.count_documents({})
        cursor = db.accounts.find({}).sort("created_at", -1).skip(skip).limit(limit)

        return {
            "accounts": [Account.serialize(doc) for doc in cursor],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 1
            }
        }

    @classmethod
    def get_account_by_id(cls, account_id: str, requesting_user: dict) -> dict:
        """
        Retrieves a single account, strictly enforcing ownership unless
        the requesting user is an administrator.
        """
        db = mongo_manager.get_db()
        account = db.accounts.find_one({"account_id": account_id})
        if not account:
            raise NotFoundError("Account not found")

        # Authorization check
        is_admin = requesting_user.get("role") == "admin"
        is_owner = account["user_id"] == requesting_user.get("user_id")

        if not (is_admin or is_owner):
            logger.warning(
                f"Unauthorized account access attempt: user {requesting_user.get('user_id')} "
                f"tried to view account {account_id} owned by {account['user_id']}"
            )
            raise AuthorizationError("You do not have permission to access this account")

        return Account.serialize(account)

    @classmethod
    def deposit(
        cls,
        account_id: str,
        amount_paise: int,
        requesting_user: dict,
        description: str = "",
        idempotency_key: str = None
    ) -> dict:
        """
        Performs an atomic deposit into a bank account.
        Increments balance atomically and writes an immutable transaction record.
        """
        user_id = requesting_user.get("user_id")
        cached = cls.check_idempotency(idempotency_key, user_id, "deposit")
        if cached:
            return cached

        db = mongo_manager.get_db()
        account = db.accounts.find_one({"account_id": account_id})
        if not account:
            raise NotFoundError("Account not found")

        # Verify access: customer must own the account, or admin
        is_admin = requesting_user.get("role") == "admin"
        is_owner = account["user_id"] == user_id
        if not (is_admin or is_owner):
            raise AuthorizationError("You do not have permission to deposit into this account")

        if account.get("status") != "ACTIVE":
            raise ValidationError(f"Account is not active (current status: {account.get('status')})")

        # Real-time ML Risk Assessment (computed before holding database write lock)
        now = datetime.now(timezone.utc)
        risk_level = "NORMAL"
        fraud_prob = 0.0
        try:
            from app.services.ml_service import MLService
            feat = MLService.extract_features_from_db(
                account_id=account_id,
                user_id=user_id,
                amount_paise=amount_paise,
                tx_type="DEPOSIT",
                tx_time=now
            )
            pred = MLService.predict_risk(feat)
            risk_level = pred["risk_level"]
            fraud_prob = pred["fraud_probability"]
        except Exception as ml_err:
            logger.warning(f"ML risk scoring skipped for deposit: {ml_err}")

        tx_status = "COMPLETED"
        if risk_level == "HIGH_RISK":
            tx_status = "FLAGGED_HIGH_RISK"
        elif risk_level == "SUSPICIOUS":
            tx_status = "FLAGGED_SUSPICIOUS"

        def _action(session):
            now_tx = datetime.now(timezone.utc)
            # Atomic balance increment
            updated_account = db.accounts.find_one_and_update(
                {"account_id": account_id, "status": "ACTIVE"},
                {"$inc": {"balance_paise": amount_paise}, "$set": {"updated_at": now_tx}},
                return_document=ReturnDocument.AFTER,
                session=session
            )

            if not updated_account:
                raise ValidationError("Failed to complete deposit. Account may be inactive.")

            # Record immutable transaction ledger entry
            tx_doc = Transaction.create_document(
                account_id=account_id,
                user_id=user_id,
                tx_type="DEPOSIT",
                amount_paise=amount_paise,
                balance_after_paise=updated_account["balance_paise"],
                status=tx_status,
                description=description or "Funds deposit",
                idempotency_key=idempotency_key,
                metadata={"executed_by": user_id, "role": requesting_user.get("role")},
                risk_level=risk_level,
                fraud_probability=fraud_prob
            )
            db.transactions.insert_one(tx_doc, session=session)

            cls.record_audit(
                action="FUNDS_DEPOSITED",
                user_id=user_id,
                account_id=account_id,
                details={
                    "amount_paise": amount_paise,
                    "new_balance_paise": updated_account["balance_paise"],
                    "tx_id": tx_doc["transaction_id"]
                },
                session=session
            )

            result = {
                "transaction": Transaction.serialize(tx_doc),
                "account": Account.serialize(updated_account)
            }
            cls.save_idempotency(idempotency_key, user_id, "deposit", result, session=session)
            return result

        result = cls._execute_in_session(_action)
        logger.info(
            f"Deposit completed: {amount_paise} paise to account {account_id} "
            f"(New balance: {result['account']['balance_paise']} paise)"
        )
        return result

    @classmethod
    def withdraw(
        cls,
        account_id: str,
        amount_paise: int,
        requesting_user: dict,
        description: str = "",
        idempotency_key: str = None
    ) -> dict:
        """
        Performs an atomic withdrawal from a bank account with strict overdraft prevention.
        Guarantees that balance cannot drop below zero via conditional atomic update.
        """
        user_id = requesting_user.get("user_id")
        cached = cls.check_idempotency(idempotency_key, user_id, "withdraw")
        if cached:
            return cached

        db = mongo_manager.get_db()
        account = db.accounts.find_one({"account_id": account_id})
        if not account:
            raise NotFoundError("Account not found")

        # Verify access: customer must own the account, or admin
        is_admin = requesting_user.get("role") == "admin"
        is_owner = account["user_id"] == user_id
        if not (is_admin or is_owner):
            raise AuthorizationError("You do not have permission to withdraw from this account")

        if account.get("status") != "ACTIVE":
            raise ValidationError(f"Account is not active (current status: {account.get('status')})")

        # Preliminary balance check for fast user feedback
        if account.get("balance_paise", 0) < amount_paise:
            cls.record_audit(
                action="WITHDRAWAL_OVERDRAFT_PREVENTED",
                user_id=user_id,
                account_id=account_id,
                status="REJECTED",
                details={
                    "requested_amount_paise": amount_paise,
                    "current_balance_paise": account.get("balance_paise", 0)
                }
            )
            raise ValidationError("Insufficient funds. Overdrafts are strictly prohibited.")

        # Real-time ML Risk Assessment (computed before holding database write lock)
        now = datetime.now(timezone.utc)
        risk_level = "NORMAL"
        fraud_prob = 0.0
        try:
            from app.services.ml_service import MLService
            feat = MLService.extract_features_from_db(
                account_id=account_id,
                user_id=user_id,
                amount_paise=amount_paise,
                tx_type="WITHDRAWAL",
                tx_time=now
            )
            pred = MLService.predict_risk(feat)
            risk_level = pred["risk_level"]
            fraud_prob = pred["fraud_probability"]
        except Exception as ml_err:
            logger.warning(f"ML risk scoring skipped for withdraw: {ml_err}")

        tx_status = "COMPLETED"
        if risk_level == "HIGH_RISK":
            tx_status = "FLAGGED_HIGH_RISK"
        elif risk_level == "SUSPICIOUS":
            tx_status = "FLAGGED_SUSPICIOUS"

        def _action(session):
            now_tx = datetime.now(timezone.utc)
            # CRITICAL ATOMIC OVERDRAFT GUARD:
            # We filter by {"balance_paise": {"$gte": amount_paise}}.
            # If concurrent withdrawals occur, only the one whose condition matches will succeed!
            updated_account = db.accounts.find_one_and_update(
                {
                    "account_id": account_id,
                    "status": "ACTIVE",
                    "balance_paise": {"$gte": amount_paise}
                },
                {"$inc": {"balance_paise": -amount_paise}, "$set": {"updated_at": now_tx}},
                return_document=ReturnDocument.AFTER,
                session=session
            )

            if not updated_account:
                # The condition {"$gte": amount_paise} was not satisfied
                raise ValidationError("Insufficient funds. Overdrafts are strictly prohibited.")

            # Record immutable transaction ledger entry
            tx_doc = Transaction.create_document(
                account_id=account_id,
                user_id=user_id,
                tx_type="WITHDRAWAL",
                amount_paise=amount_paise,
                balance_after_paise=updated_account["balance_paise"],
                status=tx_status,
                description=description or "Funds withdrawal",
                idempotency_key=idempotency_key,
                metadata={"executed_by": user_id, "role": requesting_user.get("role")},
                risk_level=risk_level,
                fraud_probability=fraud_prob
            )
            db.transactions.insert_one(tx_doc, session=session)

            cls.record_audit(
                action="FUNDS_WITHDRAWN",
                user_id=user_id,
                account_id=account_id,
                details={
                    "amount_paise": amount_paise,
                    "new_balance_paise": updated_account["balance_paise"],
                    "tx_id": tx_doc["transaction_id"]
                },
                session=session
            )

            result = {
                "transaction": Transaction.serialize(tx_doc),
                "account": Account.serialize(updated_account)
            }
            cls.save_idempotency(idempotency_key, user_id, "withdraw", result, session=session)
            return result

        result = cls._execute_in_session(_action)
        logger.info(
            f"Withdrawal completed: {amount_paise} paise from account {account_id} "
            f"(Remaining balance: {result['account']['balance_paise']} paise)"
        )
        return result

    @classmethod
    def transfer(
        cls,
        source_account_id: str,
        target_account_identifier: str,
        amount_paise: int,
        requesting_user: dict,
        description: str = "",
        idempotency_key: str = None
    ) -> dict:
        """
        Executes an atomic transfer between two accounts.
        Debits source account and credits target account within a transaction.
        """
        user_id = requesting_user.get("user_id")
        cached = cls.check_idempotency(idempotency_key, user_id, "transfer")
        if cached:
            return cached

        db = mongo_manager.get_db()
        source_account = db.accounts.find_one({"account_id": source_account_id})
        if not source_account:
            raise NotFoundError("Source account not found")

        # Authorization check
        is_admin = requesting_user.get("role") == "admin"
        if not (is_admin or source_account["user_id"] == user_id):
            raise AuthorizationError("You do not have permission to transfer funds from this account")

        # Find target account by account_number or account_id
        target_account = db.accounts.find_one({
            "$or": [
                {"account_number": target_account_identifier},
                {"account_id": target_account_identifier}
            ]
        })
        if not target_account:
            raise NotFoundError("Target account not found")

        if source_account["account_id"] == target_account["account_id"]:
            raise ValidationError("Source and destination accounts must be different")

        if source_account.get("status") != "ACTIVE" or target_account.get("status") != "ACTIVE":
            raise ValidationError("Both source and destination accounts must be active")

        if source_account.get("balance_paise", 0) < amount_paise:
            raise ValidationError("Insufficient funds in source account for transfer")

        # Real-time ML Risk Assessment for Transfer (computed before holding database write lock)
        now = datetime.now(timezone.utc)
        risk_level = "NORMAL"
        fraud_prob = 0.0
        try:
            from app.services.ml_service import MLService
            feat = MLService.extract_features_from_db(
                account_id=source_account_id,
                user_id=user_id,
                amount_paise=amount_paise,
                tx_type="TRANSFER",
                tx_time=now
            )
            pred = MLService.predict_risk(feat)
            risk_level = pred["risk_level"]
            fraud_prob = pred["fraud_probability"]
        except Exception as ml_err:
            logger.warning(f"ML risk scoring skipped for transfer: {ml_err}")

        tx_status = "COMPLETED"
        if risk_level == "HIGH_RISK":
            tx_status = "FLAGGED_HIGH_RISK"
        elif risk_level == "SUSPICIOUS":
            tx_status = "FLAGGED_SUSPICIOUS"

        def _action(session):
            now_tx = datetime.now(timezone.utc)
            # 1. Debit source account (guarded by $gte)
            updated_source = db.accounts.find_one_and_update(
                {
                    "account_id": source_account_id,
                    "status": "ACTIVE",
                    "balance_paise": {"$gte": amount_paise}
                },
                {"$inc": {"balance_paise": -amount_paise}, "$set": {"updated_at": now_tx}},
                return_document=ReturnDocument.AFTER,
                session=session
            )
            if not updated_source:
                raise ValidationError("Transfer failed: Insufficient funds in source account")

            # 2. Credit target account
            updated_target = db.accounts.find_one_and_update(
                {"account_id": target_account["account_id"], "status": "ACTIVE"},
                {"$inc": {"balance_paise": amount_paise}, "$set": {"updated_at": now_tx}},
                return_document=ReturnDocument.AFTER,
                session=session
            )
            if not updated_target:
                raise ValidationError("Transfer failed: Destination account is unavailable")

            # 3. Create debit ledger record for source
            debit_tx = Transaction.create_document(
                account_id=source_account_id,
                user_id=user_id,
                tx_type="TRANSFER",
                amount_paise=amount_paise,
                balance_after_paise=updated_source["balance_paise"],
                status=tx_status,
                description=description or f"Transfer to {target_account['account_number']}",
                counterparty_account_id=target_account["account_id"],
                idempotency_key=idempotency_key,
                metadata={"direction": "OUTGOING", "target_number": target_account["account_number"]},
                risk_level=risk_level,
                fraud_probability=fraud_prob
            )
            db.transactions.insert_one(debit_tx, session=session)

            # 4. Create credit ledger record for target
            credit_tx = Transaction.create_document(
                account_id=target_account["account_id"],
                user_id=target_account["user_id"],
                tx_type="TRANSFER",
                amount_paise=amount_paise,
                balance_after_paise=updated_target["balance_paise"],
                status="COMPLETED",
                description=description or f"Transfer from {source_account['account_number']}",
                counterparty_account_id=source_account_id,
                metadata={"direction": "INCOMING", "source_number": source_account["account_number"]}
            )
            db.transactions.insert_one(credit_tx, session=session)

            cls.record_audit(
                action="FUNDS_TRANSFERRED",
                user_id=user_id,
                account_id=source_account_id,
                details={
                    "target_account_id": target_account["account_id"],
                    "amount_paise": amount_paise,
                    "debit_tx_id": debit_tx["transaction_id"]
                },
                session=session
            )

            result = {
                "transaction": Transaction.serialize(debit_tx),
                "source_account": Account.serialize(updated_source),
                "target_account_number": target_account["account_number"]
            }
            cls.save_idempotency(idempotency_key, user_id, "transfer", result, session=session)
            return result

        result = cls._execute_in_session(_action)
        logger.info(f"Transfer completed: {amount_paise} paise from {source_account_id} to {target_account['account_id']}")
        return result

    @classmethod
    def get_account_transactions(
        cls,
        account_id: str,
        requesting_user: dict,
        page: int = 1,
        limit: int = 10,
        tx_type: str = None,
        sort_dir: str = "desc"
    ) -> dict:
        """
        Retrieves paginated transaction history for a specific account.
        Verifies ownership or administrative rights.
        """
        db = mongo_manager.get_db()
        account = db.accounts.find_one({"account_id": account_id})
        if not account:
            raise NotFoundError("Account not found")

        is_admin = requesting_user.get("role") == "admin"
        if not (is_admin or account["user_id"] == requesting_user.get("user_id")):
            raise AuthorizationError("You do not have permission to view transaction history for this account")

        query = {"account_id": account_id}
        if tx_type and tx_type.upper() in {"DEPOSIT", "WITHDRAWAL", "TRANSFER"}:
            query["type"] = tx_type.upper()

        sort_direction = -1 if sort_dir.lower() == "desc" else 1
        skip = (page - 1) * limit

        total = db.transactions.count_documents(query)
        cursor = db.transactions.find(query).sort("timestamp", sort_direction).skip(skip).limit(limit)

        return {
            "account_id": account_id,
            "transactions": [Transaction.serialize(doc) for doc in cursor],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 1
            }
        }

    @classmethod
    def get_user_transactions(
        cls,
        user_id: str,
        page: int = 1,
        limit: int = 10,
        tx_type: str = None
    ) -> dict:
        """Retrieves paginated transactions across all accounts belonging to the customer."""
        db = mongo_manager.get_db()
        query = {"user_id": user_id}
        if tx_type and tx_type.upper() in {"DEPOSIT", "WITHDRAWAL", "TRANSFER"}:
            query["type"] = tx_type.upper()

        skip = (page - 1) * limit
        total = db.transactions.count_documents(query)
        cursor = db.transactions.find(query).sort("timestamp", -1).skip(skip).limit(limit)

        return {
            "transactions": [Transaction.serialize(doc) for doc in cursor],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 1
            }
        }
