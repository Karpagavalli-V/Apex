import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.utils.logger import logger
from app.utils.errors import AuthenticationError

class MongoManager:
    """Manages MongoDB client and database access."""
    def __init__(self):
        self.client = None
        self.db = None
        self.supports_transactions = False

    def init_app(self, app):
        mongo_uri = app.config.get("MONGO_URI", "mongodb://127.0.0.1:27017")
        db_name = app.config.get("DB_NAME", "banking_dev")
        
        try:
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=2500,
                connectTimeoutMS=2500
            )
            # Verify connectivity
            hello_res = self.client.admin.command("hello")
            self.db = self.client[db_name]
            
            # Check transaction support (replica set or mongos)
            is_repl_set = bool(hello_res.get("setName"))
            is_mongos = hello_res.get("msg") == "isdbgrid"
            self.supports_transactions = is_repl_set or is_mongos
            
            logger.info(
                "Connected to MongoDB. Multi-document transactions supported: "
                f"{self.supports_transactions}"
            )
            
            # Initialize required collections and unique indexes
            self.setup_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            logger.error(f"Failed to connect to MongoDB: {err}")
            self.client = None
            self.db = None
            self.supports_transactions = False
            if not app.config.get("TESTING", False):
                # In non-testing environments, log the error clearly
                logger.warning("MongoDB is currently offline or unreachable.")

    def setup_indexes(self):
        """Ensures unique and query indexes exist on essential collections."""
        if self.db is None:
            return
        
        # 1. Users collection
        users_col = self.db.users
        users_col.create_index([("email", ASCENDING)], unique=True, name="uniq_user_email")
        users_col.create_index([("username", ASCENDING)], unique=True, name="uniq_user_username")
        users_col.create_index([("user_id", ASCENDING)], unique=True, name="uniq_user_id")
        users_col.create_index([("role", ASCENDING)], name="idx_user_role")

        # 2. Accounts collection
        accts_col = self.db.accounts
        accts_col.create_index([("account_id", ASCENDING)], unique=True, name="uniq_account_id")
        accts_col.create_index([("account_number", ASCENDING)], unique=True, name="uniq_account_number")
        accts_col.create_index([("user_id", ASCENDING)], name="idx_account_user_id")
        accts_col.create_index([("status", ASCENDING)], name="idx_account_status")

        # 3. Transactions collection
        tx_col = self.db.transactions
        tx_col.create_index([("transaction_id", ASCENDING)], unique=True, name="uniq_tx_id")
        tx_col.create_index([("account_id", ASCENDING)], name="idx_tx_account_id")
        tx_col.create_index([("user_id", ASCENDING)], name="idx_tx_user_id")
        tx_col.create_index([("timestamp", DESCENDING)], name="idx_tx_timestamp")
        tx_col.create_index([("account_id", ASCENDING), ("timestamp", DESCENDING)], name="idx_tx_acct_time")

        # 4. Idempotency keys collection (expires after 24 hours)
        idem_col = self.db.idempotency_keys
        idem_col.create_index(
            [("key", ASCENDING), ("user_id", ASCENDING)],
            unique=True,
            name="uniq_idem_key_user"
        )
        idem_col.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=86400,
            name="ttl_idem_key_24h"
        )

        # 5. Audit logs collection
        audit_col = self.db.audit_logs
        audit_col.create_index([("timestamp", DESCENDING)], name="idx_audit_timestamp")
        audit_col.create_index([("user_id", ASCENDING)], name="idx_audit_user_id")
        audit_col.create_index([("action", ASCENDING)], name="idx_audit_action")

        logger.info("MongoDB unique and query indexes verified on all Phase 2 collections.")

    def get_db(self):
        return self.db

    def is_healthy(self) -> bool:
        """Returns True if MongoDB can be pinged."""
        if self.client is None:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False


class PasswordManager:
    """Handles secure password hashing and verification using bcrypt."""
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not plain_password or not hashed_password:
            return False
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception as err:
            logger.error(f"Password verification error: {err}")
            return False


class JWTManager:
    """Handles JWT token generation and validation."""
    @staticmethod
    def generate_token(user_id: str, role: str, secret_key: str, expires_in: timedelta) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + expires_in,
            "type": "access"
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @staticmethod
    def decode_token(token: str, secret_key: str) -> dict:
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid authentication token.")


# Module instances
mongo_manager = MongoManager()
password_manager = PasswordManager()
jwt_manager = JWTManager()
