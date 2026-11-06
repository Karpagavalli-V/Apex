import os
import sys
from pathlib import Path
import pytest
from pymongo import MongoClient

# Ensure backend directory is in python path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app import create_app
from app.extensions import mongo_manager, jwt_manager
from app.models.user import User

TEST_DB_NAME = "banking_test"

@pytest.fixture(scope="session")
def app():
    """Initializes the Flask app configured specifically for testing."""
    os.environ["FLASK_ENV"] = "testing"
    os.environ["TEST_DB_NAME"] = TEST_DB_NAME
    
    flask_app = create_app("testing")
    
    # Safety assertion: verify the test suite NEVER points to the development database
    assert flask_app.config["DB_NAME"] == TEST_DB_NAME, (
        f"CRITICAL SAFETY CHECK: Test suite database must be '{TEST_DB_NAME}', "
        f"but got '{flask_app.config['DB_NAME']}'"
    )
    
    yield flask_app
    
    # Teardown: Clean up test database after all tests complete
    client = MongoClient(flask_app.config["MONGO_URI"])
    client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture(scope="function")
def client(app):
    """Provides a Flask test client for HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def clean_db(app):
    """Cleans all collections in the test database before each test run."""
    db = mongo_manager.get_db()
    if db is not None:
        db.users.delete_many({})
        db.accounts.delete_many({})
        db.transactions.delete_many({})
        db.idempotency_keys.delete_many({})
        db.audit_logs.delete_many({})
    yield


@pytest.fixture
def customer_user(app):
    """Creates a standard customer in the test database and returns details with token."""
    db = mongo_manager.get_db()
    plain_password = "CustomerPassword123!"
    user_doc = User.create_document(
        email="customer@example.com",
        username="testcustomer",
        plain_password=plain_password,
        full_name="Alice Customer",
        role="customer"
    )
    db.users.insert_one(user_doc)
    
    token = jwt_manager.generate_token(
        user_id=user_doc["user_id"],
        role=user_doc["role"],
        secret_key=app.config["JWT_SECRET_KEY"],
        expires_in=app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )
    
    return {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "username": user_doc["username"],
        "password": plain_password,
        "role": "customer",
        "token": token,
        "auth_headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def admin_user(app):
    """Creates an administrator user in the test database and returns details with token."""
    db = mongo_manager.get_db()
    plain_password = "AdminSecurePass123!"
    user_doc = User.create_document(
        email="admin@example.com",
        username="testadmin",
        plain_password=plain_password,
        full_name="Bob Administrator",
        role="admin"
    )
    db.users.insert_one(admin_doc := user_doc)
    
    token = jwt_manager.generate_token(
        user_id=admin_doc["user_id"],
        role=admin_doc["role"],
        secret_key=app.config["JWT_SECRET_KEY"],
        expires_in=app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )
    
    return {
        "user_id": admin_doc["user_id"],
        "email": admin_doc["email"],
        "username": admin_doc["username"],
        "password": plain_password,
        "role": "admin",
        "token": token,
        "auth_headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def second_customer(app):
    """Creates a distinct second customer for cross-account authorization tests."""
    db = mongo_manager.get_db()
    plain_password = "CustomerTwoPass123!"
    user_doc = User.create_document(
        email="customer2@example.com",
        username="customer_two",
        plain_password=plain_password,
        full_name="Bob Customer",
        role="customer"
    )
    db.users.insert_one(user_doc)

    token = jwt_manager.generate_token(
        user_id=user_doc["user_id"],
        role=user_doc["role"],
        secret_key=app.config["JWT_SECRET_KEY"],
        expires_in=app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )

    return {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "username": user_doc["username"],
        "password": plain_password,
        "role": "customer",
        "token": token,
        "auth_headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def customer_account(app, customer_user):
    """Creates a bank account owned by customer_user with initial balance of 1000 INR (100000 paise)."""
    from app.services.banking_service import BankingService
    result = BankingService.create_account(
        user_id=customer_user["user_id"],
        account_type="SAVINGS",
        initial_deposit_paise=100000  # 1,000 INR
    )
    return result["account"]

