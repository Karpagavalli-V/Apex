import json
from app.extensions import mongo_manager

def test_system_health(client):
    """Verifies the health check endpoint returns DB status and transaction mode."""
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["database"]["supports_transactions"] is True
    assert data["database"]["transaction_mode"] == "replica_set"


def test_customer_registration_success(client):
    """Verifies that a new customer can register successfully and receives a JWT."""
    payload = {
        "email": "jane.doe@example.com",
        "username": "janedoe",
        "password": "Password123!",
        "full_name": "Jane Doe"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    
    user = data["data"]["user"]
    assert user["email"] == "jane.doe@example.com"
    assert user["username"] == "janedoe"
    assert user["full_name"] == "Jane Doe"
    assert user["role"] == "customer"
    assert "password_hash" not in user
    assert "user_id" in user


def test_registration_accepts_hyphen_in_username(client):
    """Verifies that common hyphenated usernames are accepted."""
    res = client.post("/api/auth/register", json={
        "email": "hyphenated@example.com",
        "username": "valid-user",
        "password": "Password123!",
        "full_name": "Hyphenated User"
    })
    assert res.status_code == 201
    assert res.get_json()["data"]["user"]["username"] == "valid-user"


def test_registration_privilege_escalation_prevention(client):
    """
    CRITICAL SECURITY TEST:
    Verifies that public registration CANNOT create an admin account,
    even if the attacker explicitly submits {'role': 'admin'}.
    """
    payload = {
        "email": "hacker@example.com",
        "username": "sneaky_admin",
        "password": "HackerPassword123!",
        "full_name": "Attacker",
        "role": "admin"  # Malicious attempt to escalate role
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    
    # Must STILL be assigned 'customer', never 'admin'
    assert data["data"]["user"]["role"] == "customer"

    # Also verify in database
    db = mongo_manager.get_db()
    saved = db.users.find_one({"username": "sneaky_admin"})
    assert saved is not None
    assert saved["role"] == "customer"


def test_registration_validation_errors(client):
    """Verifies that registration fails with 400 for invalid/missing data."""
    # Invalid email
    res1 = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "username": "validuser",
        "password": "ValidPassword123!",
        "full_name": "Test User"
    })
    assert res1.status_code == 400
    assert "Invalid email address" in str(res1.get_json())

    # Password too short
    res2 = client.post("/api/auth/register", json={
        "email": "valid@example.com",
        "username": "validuser",
        "password": "123",
        "full_name": "Test User"
    })
    assert res2.status_code == 400
    assert "Password must be at least 8 characters" in str(res2.get_json())

    # Invalid username (special characters)
    res3 = client.post("/api/auth/register", json={
        "email": "valid@example.com",
        "username": "bad user!@#",
        "password": "ValidPassword123!",
        "full_name": "Test User"
    })
    assert res3.status_code == 400


def test_registration_duplicate_email(client, customer_user):
    """Verifies that registering with an already existing email returns 409 Conflict."""
    payload = {
        "email": customer_user["email"],  # Duplicate
        "username": "differentusername",
        "password": "SomePassword123!",
        "full_name": "Duplicate Email User"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"


def test_registration_duplicate_username(client, customer_user):
    """Verifies that registering with an already existing username returns 409 Conflict."""
    payload = {
        "email": "unique.email@example.com",
        "username": customer_user["username"],  # Duplicate
        "password": "SomePassword123!",
        "full_name": "Duplicate Username User"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"


def test_login_success_with_email(client, customer_user):
    """Verifies customer login using registered email address."""
    res = client.post("/api/auth/login", json={
        "identifier": customer_user["email"],
        "password": customer_user["password"]
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == customer_user["email"]


def test_login_success_with_username(client, customer_user):
    """Verifies customer login using registered username."""
    res = client.post("/api/auth/login", json={
        "identifier": customer_user["username"],
        "password": customer_user["password"]
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["username"] == customer_user["username"]


def test_login_invalid_password(client, customer_user):
    """Verifies that an incorrect password yields 401 Unauthorized."""
    res = client.post("/api/auth/login", json={
        "identifier": customer_user["username"],
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_login_nonexistent_user(client):
    """Verifies that logging in with an unknown identifier yields 401 Unauthorized."""
    res = client.post("/api/auth/login", json={
        "identifier": "nonexistent_user",
        "password": "Password123!"
    })
    assert res.status_code == 401


def test_protected_route_without_token(client):
    """Verifies calling /api/auth/me without an Authorization header returns 401."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_protected_route_invalid_token(client):
    """Verifies calling /api/auth/me with an invalid JWT returns 401."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
    assert res.status_code == 401


def test_protected_route_valid_token(client, customer_user):
    """Verifies calling /api/auth/me with a valid token returns 200 and the user profile."""
    res = client.get("/api/auth/me", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["username"] == customer_user["username"]
    assert data["data"]["user"]["email"] == customer_user["email"]


def test_change_password_flow(client, customer_user):
    """Verifies changing password updates credentials and old password is invalidated."""
    new_password = "NewStrongPassword456!"
    
    # 1. Change password
    res = client.post(
        "/api/auth/change-password",
        headers=customer_user["auth_headers"],
        json={
            "old_password": customer_user["password"],
            "new_password": new_password
        }
    )
    assert res.status_code == 200
    
    # 2. Login with old password fails
    res_old = client.post("/api/auth/login", json={
        "identifier": customer_user["username"],
        "password": customer_user["password"]
    })
    assert res_old.status_code == 401
    
    # 3. Login with new password succeeds
    res_new = client.post("/api/auth/login", json={
        "identifier": customer_user["username"],
        "password": new_password
    })
    assert res_new.status_code == 200


def test_admin_create_admin_success(client, admin_user):
    """Verifies that an existing admin can create another administrator."""
    payload = {
        "email": "second.admin@example.com",
        "username": "secondadmin",
        "password": "SecondAdmin123!",
        "full_name": "Second Administrator"
    }
    res = client.post(
        "/api/auth/admin/create-admin",
        headers=admin_user["auth_headers"],
        json=payload
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["role"] == "admin"


def test_admin_create_admin_forbidden_for_customer(client, customer_user):
    """
    CRITICAL RBAC TEST:
    Verifies that a customer is strictly forbidden (403) from calling admin endpoints.
    """
    payload = {
        "email": "unauthorized.admin@example.com",
        "username": "badadmin",
        "password": "Password123!",
        "full_name": "Unauthorized Admin"
    }
    res = client.post(
        "/api/auth/admin/create-admin",
        headers=customer_user["auth_headers"],
        json=payload
    )
    assert res.status_code == 403
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"


def test_database_isolation(client, customer_user):
    """
    SAFETY TEST:
    Verifies that test operations run strictly against 'banking_test'
    and do not pollute 'banking_dev'.
    """
    db = mongo_manager.get_db()
    assert db.name == "banking_test"
    
    # Verify user exists in banking_test
    assert db.users.find_one({"username": customer_user["username"]}) is not None
    
    # Verify banking_dev does NOT contain this test user
    dev_db = mongo_manager.client["banking_dev"]
    assert dev_db.users.find_one({"username": customer_user["username"]}) is None
