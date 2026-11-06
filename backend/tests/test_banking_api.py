import pytest
from app.extensions import mongo_manager

def test_create_account_success(client, customer_user):
    """Verifies customer can create a bank account with 0 initial balance."""
    res = client.post(
        "/api/accounts",
        headers=customer_user["auth_headers"],
        json={"account_type": "SAVINGS"}
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    
    acct = data["data"]["account"]
    assert acct["account_type"] == "SAVINGS"
    assert acct["balance_paise"] == 0
    assert acct["balance_inr"] == 0.0
    assert acct["currency"] == "INR"
    assert len(acct["account_number"]) == 12
    assert acct["status"] == "ACTIVE"
    assert acct["user_id"] == customer_user["user_id"]


def test_create_account_with_initial_deposit(client, customer_user):
    """Verifies customer can create an account with an initial deposit (in INR or paise)."""
    res = client.post(
        "/api/accounts",
        headers=customer_user["auth_headers"],
        json={
            "account_type": "CHECKING",
            "initial_deposit": 500.50  # 500.50 INR = 50050 paise
        }
    )
    assert res.status_code == 201
    data = res.get_json()
    acct = data["data"]["account"]
    assert acct["account_type"] == "CHECKING"
    assert acct["balance_paise"] == 50050
    assert acct["balance_inr"] == 500.50

    # Verify transaction ledger record created
    db = mongo_manager.get_db()
    tx = db.transactions.find_one({"account_id": acct["account_id"]})
    assert tx is not None
    assert tx["type"] == "DEPOSIT"
    assert tx["amount_paise"] == 50050


def test_list_my_accounts(client, customer_user):
    """Verifies listing all accounts owned by the authenticated customer."""
    # Create 2 accounts
    client.post("/api/accounts", headers=customer_user["auth_headers"], json={"account_type": "SAVINGS"})
    client.post("/api/accounts", headers=customer_user["auth_headers"], json={"account_type": "CHECKING"})

    res = client.get("/api/accounts", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["count"] == 2
    assert len(data["data"]["accounts"]) == 2


def test_get_account_balance(client, customer_user, customer_account):
    """Verifies dedicated balance inquiry endpoint returns accurate paise and INR."""
    res = client.get(
        f"/api/accounts/{customer_account['account_id']}/balance",
        headers=customer_user["auth_headers"]
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["account_id"] == customer_account["account_id"]
    assert data["data"]["balance_paise"] == 100000  # 1,000 INR
    assert data["data"]["balance_inr"] == 1000.0


def test_deposit_success(client, customer_user, customer_account):
    """Verifies atomic deposit into customer's account."""
    res = client.post(
        f"/api/accounts/{customer_account['account_id']}/deposit",
        headers=customer_user["auth_headers"],
        json={"amount": 250.75, "description": "Salary advance"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    
    # Balance: 100000 + 25075 = 125075 paise
    assert data["data"]["account"]["balance_paise"] == 125075
    assert data["data"]["account"]["balance_inr"] == 1250.75

    # Check ledger transaction
    tx = data["data"]["transaction"]
    assert tx["type"] == "DEPOSIT"
    assert tx["amount_paise"] == 25075
    assert tx["amount_inr"] == 250.75
    assert tx["balance_after_paise"] == 125075


def test_deposit_invalid_amounts(client, customer_user, customer_account):
    """Verifies deposit rejects negative, zero, non-numeric, or fractional paise."""
    url = f"/api/accounts/{customer_account['account_id']}/deposit"
    headers = customer_user["auth_headers"]

    # Negative amount
    res1 = client.post(url, headers=headers, json={"amount": -50.0})
    assert res1.status_code == 400

    # Zero amount
    res2 = client.post(url, headers=headers, json={"amount": 0})
    assert res2.status_code == 400

    # Fractional paise (more than 2 decimal places)
    res3 = client.post(url, headers=headers, json={"amount": 10.555})
    assert res3.status_code == 400

    # Non-numeric
    res4 = client.post(url, headers=headers, json={"amount": "invalid_money"})
    assert res4.status_code == 400


def test_withdrawal_success(client, customer_user, customer_account):
    """Verifies atomic withdrawal reduces balance accurately."""
    res = client.post(
        f"/api/accounts/{customer_account['account_id']}/withdraw",
        headers=customer_user["auth_headers"],
        json={"amount": 400.0, "description": "ATM cash withdrawal"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    
    # 100000 - 40000 = 60000 paise (600.00 INR)
    assert data["data"]["account"]["balance_paise"] == 60000
    assert data["data"]["account"]["balance_inr"] == 600.0

    tx = data["data"]["transaction"]
    assert tx["type"] == "WITHDRAWAL"
    assert tx["amount_paise"] == 40000
    assert tx["balance_after_paise"] == 60000


def test_withdrawal_insufficient_funds_overdraft_prevention(client, customer_user, customer_account):
    """
    CRITICAL OVERDRAFT SAFEGUARD TEST:
    Customer attempts to withdraw more than their current balance.
    Must return 400, prevent overdraft, leave balance untouched, and audit log.
    """
    res = client.post(
        f"/api/accounts/{customer_account['account_id']}/withdraw",
        headers=customer_user["auth_headers"],
        json={"amount": 2500.0}  # Has 1,000 INR; requested 2,500 INR
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "Insufficient funds" in data["error"]["message"]

    # Verify balance was NOT mutated in database
    db = mongo_manager.get_db()
    account_in_db = db.accounts.find_one({"account_id": customer_account["account_id"]})
    assert account_in_db["balance_paise"] == 100000

    # Verify audit log recorded the prevented overdraft
    audit = db.audit_logs.find_one({"action": "WITHDRAWAL_OVERDRAFT_PREVENTED"})
    assert audit is not None
    assert audit["status"] == "REJECTED"


def test_withdrawal_exact_balance_zero_allowed(client, customer_user, customer_account):
    """Verifies withdrawing entire balance leaves 0 paise; subsequent withdrawal fails."""
    url = f"/api/accounts/{customer_account['account_id']}/withdraw"
    headers = customer_user["auth_headers"]

    # Withdraw exactly 1000.00 INR
    res1 = client.post(url, headers=headers, json={"amount": 1000.00})
    assert res1.status_code == 200
    assert res1.get_json()["data"]["account"]["balance_paise"] == 0

    # Try withdrawing 0.01 INR (1 paisa) -> should fail with insufficient funds
    res2 = client.post(url, headers=headers, json={"amount": 0.01})
    assert res2.status_code == 400
    assert "Insufficient funds" in res2.get_json()["error"]["message"]


def test_transfer_success(client, customer_user, customer_account, second_customer):
    """Verifies transfer from customer_account to second_customer account."""
    # Create target account for second customer
    res_target = client.post(
        "/api/accounts",
        headers=second_customer["auth_headers"],
        json={"account_type": "SAVINGS"}
    )
    target_acct = res_target.get_json()["data"]["account"]

    # Transfer 300 INR (30000 paise)
    res_transfer = client.post(
        f"/api/accounts/{customer_account['account_id']}/transfer",
        headers=customer_user["auth_headers"],
        json={
            "amount": 300.0,
            "target_account": target_acct["account_number"],
            "description": "Dinner split"
        }
    )
    assert res_transfer.status_code == 200
    data = res_transfer.get_json()
    assert data["success"] is True
    assert data["data"]["source_account"]["balance_paise"] == 70000  # 1000 - 300 = 700 INR

    # Verify target account balance increased by 30000 paise
    db = mongo_manager.get_db()
    target_in_db = db.accounts.find_one({"account_id": target_acct["account_id"]})
    assert target_in_db["balance_paise"] == 30000


def test_transfer_to_same_account_rejected(client, customer_user, customer_account):
    """Verifies transferring to oneself on the same account is rejected."""
    res = client.post(
        f"/api/accounts/{customer_account['account_id']}/transfer",
        headers=customer_user["auth_headers"],
        json={
            "amount": 100.0,
            "target_account": customer_account["account_number"]
        }
    )
    assert res.status_code == 400
    assert "must be different" in res.get_json()["error"]["message"]


def test_idempotency_deposit_prevents_duplicate_processing(client, customer_user, customer_account):
    """
    IDEMPOTENCY TEST:
    A client retries a deposit request with the same Idempotency-Key.
    The second request must return 200 OK with cached response,
    and the account must NOT be credited twice.
    """
    idempotency_key = "test-deposit-idem-key-001"
    url = f"/api/accounts/{customer_account['account_id']}/deposit"
    headers = {**customer_user["auth_headers"], "Idempotency-Key": idempotency_key}
    payload = {"amount": 500.0}

    # First request
    res1 = client.post(url, headers=headers, json=payload)
    assert res1.status_code == 200
    assert res1.get_json()["data"]["account"]["balance_paise"] == 150000  # 1000 + 500 = 1500 INR

    # Second request with identical Idempotency-Key
    res2 = client.post(url, headers=headers, json=payload)
    assert res2.status_code == 200
    # Response must match previous
    assert res2.get_json()["data"]["account"]["balance_paise"] == 150000

    # Check database: balance must still be 150000, not 200000!
    db = mongo_manager.get_db()
    account_in_db = db.accounts.find_one({"account_id": customer_account["account_id"]})
    assert account_in_db["balance_paise"] == 150000


def test_idempotency_withdrawal_prevents_duplicate_charge(client, customer_user, customer_account):
    """
    IDEMPOTENCY TEST:
    A client retries a withdrawal request with the same Idempotency-Key.
    The account must be debited ONLY ONCE.
    """
    idempotency_key = "test-withdraw-idem-key-002"
    url = f"/api/accounts/{customer_account['account_id']}/withdraw"
    headers = {**customer_user["auth_headers"], "Idempotency-Key": idempotency_key}
    payload = {"amount": 200.0}

    # First request: balance 1000 - 200 = 800 INR (80000 paise)
    res1 = client.post(url, headers=headers, json=payload)
    assert res1.status_code == 200
    assert res1.get_json()["data"]["account"]["balance_paise"] == 80000

    # Second request: identical Idempotency-Key
    res2 = client.post(url, headers=headers, json=payload)
    assert res2.status_code == 200
    assert res2.get_json()["data"]["account"]["balance_paise"] == 80000

    # Database balance must strictly be 80000, not 60000!
    db = mongo_manager.get_db()
    account_in_db = db.accounts.find_one({"account_id": customer_account["account_id"]})
    assert account_in_db["balance_paise"] == 80000


def test_unauthorized_access_another_customer_account(client, customer_account, second_customer):
    """
    AUTHORIZATION & OWNERSHIP TEST:
    Customer B attempts to access, deposit into, or withdraw from Customer A's account.
    All operations must return 403 Forbidden.
    """
    target_id = customer_account["account_id"]
    headers_b = second_customer["auth_headers"]

    # Customer B tries to view Customer A's account details
    res_view = client.get(f"/api/accounts/{target_id}", headers=headers_b)
    assert res_view.status_code == 403

    # Customer B tries to view Customer A's balance
    res_bal = client.get(f"/api/accounts/{target_id}/balance", headers=headers_b)
    assert res_bal.status_code == 403

    # Customer B tries to withdraw from Customer A's account
    res_with = client.post(f"/api/accounts/{target_id}/withdraw", headers=headers_b, json={"amount": 100})
    assert res_with.status_code == 403

    # Customer B tries to deposit into Customer A's account without permission
    res_dep = client.post(f"/api/accounts/{target_id}/deposit", headers=headers_b, json={"amount": 100})
    assert res_dep.status_code == 403


def test_admin_can_view_any_customer_account_and_list_all(client, customer_account, admin_user):
    """Verifies that an administrator can view any account and list all accounts."""
    # Admin views customer account
    res_view = client.get(
        f"/api/accounts/{customer_account['account_id']}",
        headers=admin_user["auth_headers"]
    )
    assert res_view.status_code == 200
    assert res_view.get_json()["data"]["account"]["account_id"] == customer_account["account_id"]

    # Admin lists all accounts
    res_all = client.get("/api/accounts/all", headers=admin_user["auth_headers"])
    assert res_all.status_code == 200
    data = res_all.get_json()
    assert data["success"] is True
    assert "accounts" in data["data"]
    assert data["data"]["pagination"]["total_count"] >= 1


def test_customer_cannot_call_admin_list_all(client, customer_user):
    """Verifies that regular customers cannot call the admin /api/accounts/all endpoint (403)."""
    res = client.get("/api/accounts/all", headers=customer_user["auth_headers"])
    assert res.status_code == 403


def test_transaction_history_pagination_and_filter(client, customer_user, customer_account):
    """Verifies pagination and filtering of transaction history."""
    url_dep = f"/api/accounts/{customer_account['account_id']}/deposit"
    url_with = f"/api/accounts/{customer_account['account_id']}/withdraw"
    headers = customer_user["auth_headers"]

    # Generate 6 deposits and 4 withdrawals
    for i in range(6):
        client.post(url_dep, headers=headers, json={"amount": 50.0, "description": f"Deposit #{i+1}"})
    for i in range(4):
        client.post(url_with, headers=headers, json={"amount": 20.0, "description": f"Withdrawal #{i+1}"})

    # Account initially had 1 deposit (initial 1,000 INR), plus 6 deposits + 4 withdrawals = 11 transactions
    url_history = f"/api/accounts/{customer_account['account_id']}/transactions"

    # Page 1, limit 5
    res_p1 = client.get(f"{url_history}?page=1&limit=5", headers=headers)
    assert res_p1.status_code == 200
    data_p1 = res_p1.get_json()["data"]
    assert len(data_p1["transactions"]) == 5
    assert data_p1["pagination"]["total_count"] == 11
    assert data_p1["pagination"]["total_pages"] == 3

    # Filter by type=WITHDRAWAL
    res_w = client.get(f"{url_history}?type=WITHDRAWAL", headers=headers)
    assert res_w.status_code == 200
    data_w = res_w.get_json()["data"]
    assert data_w["pagination"]["total_count"] == 4
    for tx in data_w["transactions"]:
        assert tx["type"] == "WITHDRAWAL"

    # Aggregated user history endpoint
    res_user_tx = client.get("/api/transactions/my-history", headers=headers)
    assert res_user_tx.status_code == 200
    assert res_user_tx.get_json()["data"]["pagination"]["total_count"] == 11


def test_multi_document_transaction_rollback_on_failure(client, customer_user, customer_account, second_customer, monkeypatch):
    """
    ACID TRANSACTION ROLLBACK TEST:
    Verifies that if an error occurs mid-way through a multi-document operation
    (e.g., after debiting the source account but before finishing the transfer),
    MongoDB rolls back the entire transaction. The source account balance must NOT be debited.
    """
    db = mongo_manager.get_db()
    source_id = customer_account["account_id"]
    initial_source_balance = customer_account["balance_paise"]  # 100000 paise (1,000 INR)

    # 1. Create a target account for second_customer with initial 500 INR (50000 paise)
    res_target = client.post(
        "/api/accounts",
        headers=second_customer["auth_headers"],
        json={"account_type": "SAVINGS", "initial_deposit": 500.0}
    )
    assert res_target.status_code == 201
    target_acct = res_target.get_json()["data"]["account"]
    target_id = target_acct["account_id"]

    # Record initial counts
    initial_tx_count = db.transactions.count_documents({})

    # 2. Monkeypatch Transaction.create_document to raise an exception when called during the transfer
    # This simulates a database or server crash right after balance modifications inside the transaction
    from app.models.transaction import Transaction
    original_create_doc = Transaction.create_document

    call_count = {"count": 0}
    def fail_mid_transaction(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] >= 1:
            raise RuntimeError("Simulated mid-transaction failure after account balance updates")
        return original_create_doc(*args, **kwargs)

    monkeypatch.setattr(Transaction, "create_document", fail_mid_transaction)

    # 3. Attempt the transfer of 300 INR (30000 paise)
    res_transfer = client.post(
        f"/api/accounts/{source_id}/transfer",
        headers=customer_user["auth_headers"],
        json={
            "amount": 300.0,
            "target_account": target_acct["account_number"],
            "description": "Failing transfer"
        }
    )

    # The request should fail with 500 due to the simulated exception
    assert res_transfer.status_code == 500

    # 4. CRITICAL VERIFICATION:
    # Source balance must STILL be 100000 paise (it must NOT have been deducted to 70000)
    source_in_db = db.accounts.find_one({"account_id": source_id})
    assert source_in_db["balance_paise"] == initial_source_balance

    # Target balance must STILL be 50000 paise (it must NOT have been credited to 80000)
    target_in_db = db.accounts.find_one({"account_id": target_id})
    assert target_in_db["balance_paise"] == 50000

    # No uncommitted or partial transaction documents should exist in transactions collection
    final_tx_count = db.transactions.count_documents({})
    # Only the initial deposit of target account should be there; no transfer records
    assert final_tx_count == initial_tx_count

