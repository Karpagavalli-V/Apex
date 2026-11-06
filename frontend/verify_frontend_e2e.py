"""
End-to-end integration and API verification test for the React frontend client.
Uses Python's standard library (urllib, json) to test all backend routes
that the frontend components connect to.
"""
import uuid
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000/api"

def make_req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    headers.setdefault("Content-Type", "application/json")
    
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return err.code, parsed

def test_full_frontend_integration():
    results = {}

    print("=== STEP 1: AUTHENTICATION & SESSION HANDLING ===")
    status, login_res = make_req(f"{BASE_URL}/auth/login", method="POST", data={
        "identifier": "mluser1",
        "password": "Password123!"
    })
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["data"]["access_token"]
    user = login_res["data"]["user"]
    print(f"[PASS] Login successful for: {user['username']} ({user['role']})")
    results["login"] = "PASS"

    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Verify Session (/auth/me)
    status, me_res = make_req(f"{BASE_URL}/auth/me", headers=auth_headers)
    assert status == 200, f"/auth/me failed: {me_res}"
    print(f"[PASS] Session verified for user_id: {me_res['data']['user']['user_id']}")
    results["auth_me"] = "PASS"

    print("\n=== STEP 2: ACCOUNTS LISTING & BALANCE DISPLAY ===")
    status, accts_res = make_req(f"{BASE_URL}/accounts", headers=auth_headers)
    assert status == 200, f"Get accounts failed: {accts_res}"
    accounts = accts_res["data"]["accounts"]
    if len(accounts) == 0:
        print("[INFO] User has 0 accounts. Creating primary SAVINGS account with initial deposit of INR 10,000.00...")
        ca_idem = str(uuid.uuid4())
        status, ca_res = make_req(
            f"{BASE_URL}/accounts",
            method="POST",
            headers={**auth_headers, "Idempotency-Key": ca_idem},
            data={"account_type": "SAVINGS", "initial_deposit": 10000.0}
        )
        assert status == 201, f"Failed to create account: {ca_res}"
        primary_acc = ca_res["data"]["account"]
        accounts = [primary_acc]
    else:
        primary_acc = accounts[0]
    print(f"[PASS] Found {len(accounts)} accounts. Primary: {primary_acc['account_number']} ({primary_acc['account_type']}) Balance: INR {primary_acc['balance_paise'] / 100:.2f}")
    results["accounts_list"] = f"PASS ({len(accounts)} accounts)"

    print("\n=== STEP 3: BANKING OPERATIONS (DEPOSIT, WITHDRAW, TRANSFER, IDEMPOTENCY) ===")
    # Deposit
    dep_idem = str(uuid.uuid4())
    dep_headers = {**auth_headers, "Idempotency-Key": dep_idem}
    status, dep_res = make_req(
        f"{BASE_URL}/accounts/{primary_acc['account_id']}/deposit",
        method="POST",
        headers=dep_headers,
        data={
            "amount": 500.0,
            "description": "Frontend Phase 5 automated verification deposit"
        }
    )
    assert status == 200, f"Deposit failed: {dep_res}"
    dep_data = dep_res["data"]
    new_balance = dep_data["account"]["balance_paise"]
    print(f"[PASS] Deposit of INR 500.00 successful. New balance: INR {new_balance / 100:.2f}. Risk: {dep_data['transaction'].get('risk_level', 'NORMAL')}")
    results["deposit"] = "PASS"

    # Duplicate deposit (Idempotency test)
    status, dup_res = make_req(
        f"{BASE_URL}/accounts/{primary_acc['account_id']}/deposit",
        method="POST",
        headers=dep_headers,
        data={
            "amount": 500.0,
            "description": "Duplicate deposit attempt"
        }
    )
    assert status == 200, f"Idempotent duplicate failed: {dup_res}"
    assert dup_res["data"]["account"]["balance_paise"] == new_balance, "Idempotency violated on duplicate deposit"
    print("[PASS] Idempotency protection verified: duplicate request safely returned identical state without double balance increase.")
    results["idempotency_deposit"] = "PASS"

    # Withdrawal
    w_idem = str(uuid.uuid4())
    w_headers = {**auth_headers, "Idempotency-Key": w_idem}
    status, w_res = make_req(
        f"{BASE_URL}/accounts/{primary_acc['account_id']}/withdraw",
        method="POST",
        headers=w_headers,
        data={
            "amount": 100.0,
            "description": "Frontend Phase 5 automated verification withdrawal"
        }
    )
    assert status == 200, f"Withdrawal failed: {w_res}"
    print(f"[PASS] Withdrawal of INR 100.00 successful. Remaining: INR {w_res['data']['account']['balance_paise'] / 100:.2f}")
    results["withdraw"] = "PASS"

    # Overdraft Prevention Test
    od_idem = str(uuid.uuid4())
    od_headers = {**auth_headers, "Idempotency-Key": od_idem}
    status, od_res = make_req(
        f"{BASE_URL}/accounts/{primary_acc['account_id']}/withdraw",
        method="POST",
        headers=od_headers,
        data={
            "amount": 99999999.0,
            "description": "Overdraft attack attempt"
        }
    )
    assert status in [400, 422], f"Overdraft was not blocked: {status} {od_res}"
    print(f"[PASS] Overdraft prevention verified: excessive withdrawal blocked with status {status}.")
    results["overdraft_prevention"] = "PASS"

    # Inter-Account Transfer
    if len(accounts) >= 2:
        dest_acc = accounts[1]
    else:
        ca_idem = str(uuid.uuid4())
        status, ca_res = make_req(
            f"{BASE_URL}/accounts",
            method="POST",
            headers={**auth_headers, "Idempotency-Key": ca_idem},
            data={"account_type": "CHECKING", "initial_deposit": 100.0}
        )
        assert status == 201, f"Failed to create secondary account: {ca_res}"
        dest_acc = ca_res["data"]["account"]

    t_idem = str(uuid.uuid4())
    t_headers = {**auth_headers, "Idempotency-Key": t_idem}
    status, t_res = make_req(
        f"{BASE_URL}/accounts/{primary_acc['account_id']}/transfer",
        method="POST",
        headers=t_headers,
        data={
            "target_account": dest_acc["account_number"],
            "amount": 50.0,
            "description": "Frontend Phase 5 verification transfer"
        }
    )
    assert status == 200, f"Transfer failed: {t_res}"
    print(f"[PASS] Transfer of INR 50.00 to {dest_acc['account_number']} successful.")
    results["transfer"] = "PASS"

    print("\n=== STEP 4: TRANSACTION HISTORY & DETAILS ===")
    status, tx_res = make_req(f"{BASE_URL}/transactions/my-history?page=1&limit=5", headers=auth_headers)
    assert status == 200, f"Transaction history failed: {tx_res}"
    txs = tx_res["data"]["transactions"]
    assert len(txs) > 0, "No transactions found"
    sample_tx = txs[0]
    print(f"[PASS] Loaded {len(txs)} recent transactions. Latest: {sample_tx['transaction_id']} ({sample_tx['type']})")
    results["transactions_history"] = f"PASS ({len(txs)} loaded)"

    # Get single transaction detail
    status, dt_res = make_req(f"{BASE_URL}/transactions/{sample_tx['transaction_id']}", headers=auth_headers)
    assert status == 200, f"Transaction detail failed: {dt_res}"
    print(f"[PASS] Transaction detail audit verified for {sample_tx['transaction_id']}")
    results["transaction_detail"] = "PASS"

    print("\n=== STEP 5: FRAUD MONITORING & ML PREDICTOR ===")
    status, info_res = make_req(f"{BASE_URL}/ml/model-info", headers=auth_headers)
    assert status == 200, f"ML model info failed: {info_res}"
    ml_info = info_res["data"]
    metrics = ml_info.get("evaluation_summary") or ml_info.get("metrics") or {}
    print(f"[PASS] ML Model Info loaded: Accuracy={metrics.get('accuracy', 0)*100:.2f}%, Precision={metrics.get('precision', 0)*100:.2f}%, Recall={metrics.get('recall', 0)*100:.2f}%, F1={metrics.get('f1_score', 0):.4f}")
    results["ml_model_info"] = "PASS"

    # Test Live ML Predictor
    status, pred_res = make_req(
        f"{BASE_URL}/ml/predict-risk",
        method="POST",
        headers=auth_headers,
        data={
            "account_id": primary_acc["account_id"],
            "amount": 75000.0,
            "tx_type": "TRANSFER"
        }
    )
    assert status == 200, f"ML predict failed: {pred_res}"
    pred_data = pred_res["data"].get("prediction") or pred_res["data"]
    print(f"[PASS] ML Live Prediction: Amount=INR 75,000, Type=TRANSFER -> Risk={pred_data['risk_level']}, Prob={pred_data['fraud_probability']*100:.2f}%")
    results["ml_predict_risk"] = f"PASS ({pred_data['risk_level']})"

    print("\n=== STEP 6: AI FINANCIAL ASSISTANT ENDPOINTS ===")
    # 1. Summary
    status, sum_res = make_req(f"{BASE_URL}/ai/financial-summary", headers=auth_headers)
    assert status == 200, f"AI summary failed: {sum_res}"
    cur_m = sum_res["data"].get("metrics") or sum_res["data"].get("current_month") or {}
    dep_val = (cur_m.get("total_deposits_paise", 0) or (cur_m.get("total_deposits_inr", 0) * 100)) / 100
    out_val = ((cur_m.get("total_withdrawals_paise", 0) + cur_m.get("total_transfers_paise", 0)) or (cur_m.get("total_outflow_inr", 0) * 100)) / 100
    print(f"[PASS] AI Financial Summary: Month={cur_m.get('month', 'current')}, Inflows=INR {dep_val:.2f}, Outflows=INR {out_val:.2f}")
    results["ai_financial_summary"] = "PASS"

    # 2. Spending Analysis
    status, sp_res = make_req(f"{BASE_URL}/ai/spending-analysis?days=30", headers=auth_headers)
    assert status == 200, f"AI spending analysis failed: {sp_res}"
    sp_data = sp_res["data"].get("metrics") or sp_res["data"]
    spent_val = (sp_data.get("total_spent_paise", 0) or (sp_data.get("total_outflow_inr", 0) * 100)) / 100
    vel_val = (sp_data.get("daily_spending_velocity_paise", 0) or (sp_data.get("daily_velocity_inr", 0) * 100)) / 100
    print(f"[PASS] AI Spending Analysis (30d): Total spent=INR {spent_val:.2f}, Velocity=INR {vel_val:.2f}/day")
    results["ai_spending_analysis"] = "PASS"

    # 3. Savings Suggestions
    status, sav_res = make_req(f"{BASE_URL}/ai/savings-suggestions", headers=auth_headers)
    assert status == 200, f"AI savings suggestions failed: {sav_res}"
    sav_data = sav_res["data"].get("metrics") or sav_res["data"]
    target_val = (sav_data.get("target_emergency_fund_paise", 0) or (sav_data.get("emergency_fund_target_inr", 0) * 100)) / 100
    runway_val = sav_data.get("coverage_months", 0) or sav_data.get("current_runway_months", 0)
    print(f"[PASS] AI Savings Suggestions: Emergency Target=INR {target_val:.2f}, Runway={runway_val:.1f} months")
    results["ai_savings_suggestions"] = "PASS"

    # 4. Chat Conversational
    status, chat_res = make_req(
        f"{BASE_URL}/ai/chat",
        method="POST",
        headers=auth_headers,
        data={"message": "Summarize my spending and tell me how I can save more."}
    )
    assert status == 200, f"AI chat failed: {chat_res}"
    chat_text = chat_res["data"].get("reply") or chat_res["data"].get("response") or ""
    is_fallback = chat_res["data"].get("is_fallback", False)
    print(f"[PASS] AI Chat Response received ({len(chat_text)} chars). Fallback: {is_fallback}")
    results["ai_chat"] = "PASS"

    print("\n================ TEST SUMMARY ================")
    for k, v in results.items():
        print(f"  {k:25}: {v}")
    print("ALL API INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_full_frontend_integration()
