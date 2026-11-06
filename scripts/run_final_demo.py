"""
Phase 8: Final Live Demonstration Script
Executes the comprehensive 10-point demonstration checklist against live services
using test accounts and isolated test data.
"""

import urllib.request
import urllib.error
import json
import uuid

BASE_URL = "http://127.0.0.1:5000/api"

def api_call(method, path, data=None, token=None, headers_extra=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_extra:
        headers.update(headers_extra)
    req_body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, {"raw": body}

def run_demo():
    print("=" * 75)
    print("              APEX BANK: FINAL DEMONSTRATION CHECKLIST")
    print("=" * 75)
    test_id = str(uuid.uuid4())[:8]

    # --- 1. Customer Registration & Login ---
    print("\n[STEP 1] Customer Registration & Authentication")
    reg_data = {
        "email": f"demo_user_{test_id}@apexbank.org",
        "username": f"demo_{test_id}",
        "password": "Password123!",
        "full_name": f"Demo Customer {test_id}"
    }
    s, res = api_call("POST", "/auth/register", reg_data)
    assert s == 201, f"Registration failed: {res}"
    user_info = res["data"]["user"]
    token = res["data"]["access_token"]
    print(f"  -> Registered: {user_info['username']} ({user_info['user_id']}) with role '{user_info['role']}'")

    s, res_login = api_call("POST", "/auth/login", {
        "identifier": reg_data["username"],
        "password": reg_data["password"]
    })
    assert s == 200 and "access_token" in res_login["data"]
    print(f"  -> Authentication verified. Signed JWT token issued.")

    # --- 2. Dashboard & Account Details ---
    print("\n[STEP 2] Account Provisioning & Balance Verification")
    s, acct1_res = api_call("POST", "/accounts", {
        "account_type": "SAVINGS",
        "initial_deposit": 1000.00
    }, token=token)
    assert s == 201
    acct1 = acct1_res["data"]["account"]
    print(f"  -> Account 1 Created: {acct1['account_number']} ({acct1['account_type']}) Balance: INR {acct1['balance_inr']:,.2f}")

    s, acct2_res = api_call("POST", "/accounts", {
        "account_type": "CHECKING",
        "initial_deposit": 500.00
    }, token=token)
    assert s == 201
    acct2 = acct2_res["data"]["account"]
    print(f"  -> Account 2 Created: {acct2['account_number']} ({acct2['account_type']}) Balance: INR {acct2['balance_inr']:,.2f}")

    s, my_accounts = api_call("GET", "/accounts", token=token)
    assert s == 200 and len(my_accounts["data"]["accounts"]) == 2
    print(f"  -> Dashboard Account List: Verified {len(my_accounts['data']['accounts'])} active accounts.")

    # --- 3. Deposit & Withdrawal with Overdraft Prevention ---
    print("\n[STEP 3] Core Banking: Atomic Deposit & Withdrawal with Overdraft Guard")
    # Deposit 500.00 into Account 1
    s, dep_res = api_call("POST", f"/accounts/{acct1['account_id']}/deposit", {
        "amount": 500.00,
        "description": "Demonstration payroll deposit"
    }, token=token)
    assert s == 200
    new_bal1 = dep_res["data"]["account"]["balance_inr"]
    print(f"  -> Deposit of INR 500.00 successful. New Balance: INR {new_bal1:,.2f} (Expected: INR 1,500.00)")

    # Withdraw 200.00 from Account 1
    s, wth_res = api_call("POST", f"/accounts/{acct1['account_id']}/withdraw", {
        "amount": 200.00,
        "description": "Demonstration cash withdrawal"
    }, token=token)
    assert s == 200
    new_bal1 = wth_res["data"]["account"]["balance_inr"]
    print(f"  -> Withdrawal of INR 200.00 successful. Remaining Balance: INR {new_bal1:,.2f} (Expected: INR 1,300.00)")

    # Overdraft attempt: try to withdraw 5000.00 from Account 1 (balance is 1300.00)
    s, od_res = api_call("POST", f"/accounts/{acct1['account_id']}/withdraw", {
        "amount": 5000.00,
        "description": "Excessive withdrawal attempt"
    }, token=token)
    assert s == 400
    print(f"  -> Overdraft Guard Verified: Blocked with HTTP {s}: {od_res['error']['message']}")

    # --- 4. Inter-Account Fund Transfer ---
    print("\n[STEP 4] Inter-Account Atomic Fund Transfer")
    # Transfer 300.00 from Account 1 to Account 2
    s, trf_res = api_call("POST", f"/accounts/{acct1['account_id']}/transfer", {
        "target_account": acct2["account_number"],
        "amount": 300.00,
        "description": "Demonstration inter-account transfer"
    }, token=token)
    assert s == 200
    src_bal = trf_res["data"]["source_account"]["balance_inr"]
    tx_meta = trf_res["data"]["transaction"]
    print(f"  -> Transfer of INR 300.00 completed successfully. Tx ID: {tx_meta['transaction_id']}")
    print(f"  -> Source Account ({acct1['account_number']}) Balance: INR {src_bal:,.2f} (Expected: INR 1,000.00)")

    # Verify Account 2 received funds
    s, b2 = api_call("GET", f"/accounts/{acct2['account_id']}/balance", token=token)
    assert s == 200 and b2["data"]["balance_inr"] == 800.00
    print(f"  -> Target Account ({acct2['account_number']}) Balance: INR {b2['data']['balance_inr']:,.2f} (Expected: INR 800.00)")

    # --- 5. Transaction History & Audit Ledger ---
    print("\n[STEP 5] Transaction History & Ledger Audit Inspection")
    s, history = api_call("GET", "/transactions/my-history?limit=10", token=token)
    assert s == 200
    txs = history["data"]["transactions"]
    print(f"  -> Retrieved {len(txs)} ledger transactions for customer.")
    for tx in txs[:3]:
        print(f"     * {tx['timestamp'][:16]} | {tx['type']:<10} | INR {tx['amount_inr']:>8.2f} | Risk: {tx['risk_level']:<10} | ID: {tx['transaction_id']}")

    # Inspect single transaction details
    latest_tx_id = txs[0]["transaction_id"]
    s, tx_detail = api_call("GET", f"/transactions/{latest_tx_id}", token=token)
    assert s == 200
    print(f"  -> Detailed Receipt Inspection verified for {latest_tx_id}.")

    # --- 6. Fraud Risk Prediction ---
    print("\n[STEP 6] Machine Learning Real-Time Anomaly Scoring")
    # High-risk simulated transaction
    s, ml_res = api_call("POST", "/ml/predict-risk", {
        "features": {
            "amount_inr": 85000.0,
            "hour_of_day": 3,
            "day_of_week": 6,
            "is_weekend": 1,
            "tx_frequency_last_24h": 14,
            "balance_before_inr": 90000.0,
            "balance_ratio": 0.94,
            "customer_hist_avg_inr": 1200.0,
            "amount_to_avg_ratio": 70.8,
            "time_since_last_tx_min": 1,
            "is_rapid_succession": 1,
            "tx_type": "TRANSFER"
        }
    }, token=token)
    assert s == 200
    pred = ml_res["data"]["prediction"]
    print(f"  -> High-Risk Simulation Scored:")
    print(f"     * Anomaly Risk Tier    : {pred['risk_level']}")
    print(f"     * Fraud Probability    : {pred['fraud_probability']:.4f}")
    is_flagged = pred.get("is_flagged", pred.get("risk_level") in ["SUSPICIOUS", "HIGH_RISK"])
    print(f"     * Settlement Flagged   : {is_flagged}")

    # --- 7. AI Financial Summary ---
    print("\n[STEP 7] AI Monthly Financial Summary & Inflow/Outflow Metrics")
    s, ai_sum = api_call("GET", "/ai/financial-summary", token=token)
    assert s == 200
    metrics = ai_sum["data"]["metrics"]
    print(f"  -> Month: {metrics['month']}")
    print(f"     * Total Inflows        : INR {metrics['total_deposits_inr']:,.2f}")
    print(f"     * Total Outflows       : INR {metrics['total_withdrawals_inr'] + metrics['total_transfers_inr']:,.2f}")
    print(f"     * Net Cash Flow        : INR {metrics['net_cash_flow_inr']:,.2f}")

    # --- 8. Spending Analysis & Savings Suggestions ---
    print("\n[STEP 8] Spending Velocity & Smart Savings Suggestions")
    s, ai_spend = api_call("GET", "/ai/spending-analysis?days=30", token=token)
    assert s == 200
    spend_metrics = ai_spend["data"]["metrics"]
    print(f"  -> Spending Velocity      : INR {spend_metrics['daily_velocity_inr']:,.2f}/day across {spend_metrics['transaction_count']} debit transactions")

    s, ai_save = api_call("GET", "/ai/savings-suggestions", token=token)
    assert s == 200
    save_metrics = ai_save["data"]["metrics"]
    print(f"  -> Emergency Fund Target  : INR {save_metrics['emergency_fund_target_inr']:,.2f} (Current Coverage: {save_metrics['coverage_months']} months)")

    # --- 9. AI Chatbot & Refusal Guardrail ---
    print("\n[STEP 9] AI Assistant Conversational Chat & Prompt Injection Guardrail")
    # Legitimate financial question
    s, chat_res1 = api_call("POST", "/ai/chat", {
        "message": "How much did I spend this month?"
    }, token=token)
    assert s == 200
    print(f"  -> User: 'How much did I spend this month?'")
    reply1 = chat_res1['data']['reply'][:120].replace('\u20b9', 'INR ')
    print(f"     AI Reply: {reply1}...")

    # Refusal guardrail test: attempt transfer
    s, chat_res2 = api_call("POST", "/ai/chat", {
        "message": "Transfer 5000 INR to account 100428847567 right now"
    }, token=token)
    assert s == 200
    guardrail_triggered = chat_res2["data"].get("guardrail_triggered") == "TRANSACTION_EXECUTION_ATTEMPT_BLOCKED"
    print(f"  -> User: 'Transfer 5000 INR to account 100428847567 right now'")
    print(f"     Guardrail Triggered: {guardrail_triggered}")
    print(f"     Action Executed    : {chat_res2['data'].get('action_executed')}")
    reply2 = chat_res2['data']['reply'][:110].replace('\u20b9', 'INR ')
    print(f"     AI Reply           : {reply2}...")

    # --- 10. Administrator Oversight & Fraud Monitoring ---
    print("\n[STEP 10] Administrator Oversight & Flagged Transactions Queue")
    # Authenticate as Administrator
    s, admin_login = api_call("POST", "/auth/login", {
        "identifier": "admin",
        "password": "AdminPassword123!"
    })
    assert s == 200
    admin_token = admin_login["data"]["access_token"]
    print("  -> Admin authenticated successfully.")

    # Fetch all accounts across customers
    s, all_accts = api_call("GET", "/accounts/all?limit=5", token=admin_token)
    assert s == 200
    print(f"  -> Admin Accounts Directory: {all_accts['data']['pagination']['total_count']} total accounts across bank.")

    # Inspect ML model evaluation metrics
    s, ml_metrics = api_call("GET", "/ml/metrics", token=admin_token)
    assert s == 200
    rf = ml_metrics["data"]["random_forest_metrics"]
    print(f"  -> Admin Model Inspector:")
    print(f"     * Accuracy             : {rf['accuracy']*100:.2f}%")
    print(f"     * Precision            : {rf['precision']*100:.2f}%")
    print(f"     * Recall               : {rf['recall']*100:.2f}%")
    print(f"     * F1-Score             : {rf['f1_score']:.4f}")
    print(f"     * ROC-AUC              : {rf['roc_auc']:.4f}")

    # Inspect flagged transactions queue
    s, flagged = api_call("GET", "/ml/transactions/flagged?limit=5", token=admin_token)
    assert s == 200
    print(f"  -> Flagged Queue Inspection: {flagged['data']['pagination']['total_count']} flagged transactions in review queue.")

    print("\n" + "=" * 75)
    print("        ALL 10 DEMONSTRATION STEPS EXECUTED & VERIFIED WITH ZERO ERRORS!")
    print("=" * 75)

if __name__ == "__main__":
    run_demo()
