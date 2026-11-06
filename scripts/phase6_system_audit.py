"""
Phase 6: Full System Integration, Security, Reliability and Concurrency Audit
Executes comprehensive automated tests against live services.
"""

import sys
import os
import json
import uuid
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:5000/api"

# Helper for HTTP requests
def api_request(method, endpoint, data=None, token=None, headers_extra=None):
    url = f"{BASE_URL}{endpoint}"
    req_headers = {"Content-Type": "application/json"}
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
    if headers_extra:
        req_headers.update(headers_extra)

    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            parsed = json.loads(res_body) if res_body else {}
            return res.status, parsed, dict(res.headers)
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return err.code, parsed, dict(err.headers)
    except Exception as err:
        return 0, {"error": str(err)}, {}

class AuditRunner:
    def __init__(self):
        self.results = []
        self.test_id = str(uuid.uuid4())[:8]
        self.admin_token = None
        self.cust_a_token = None
        self.cust_a_id = None
        self.cust_b_token = None
        self.cust_b_id = None
        self.acct_a1 = None
        self.acct_a2 = None
        self.acct_b1 = None

    def record(self, category, name, passed, details=""):
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {category} -> {name}: {details}")
        self.results.append({
            "category": category,
            "name": name,
            "passed": passed,
            "details": details
        })

    def setup_test_users(self):
        print("\n--- Initializing Isolated Audit Test Entities ---")
        # 1. Login admin
        status, body, _ = api_request("POST", "/auth/login", {
            "identifier": "admin",
            "password": "AdminPassword123!"
        })
        if status == 200:
            self.admin_token = body["data"]["access_token"]
            print("  Admin authenticated successfully.")
        else:
            raise RuntimeError(f"Admin authentication failed: {body}")

        # 2. Register Customer A
        username_a = f"audit_a_{self.test_id}"
        email_a = f"audit_a_{self.test_id}@apexbank.org"
        status, body, _ = api_request("POST", "/auth/register", {
            "email": email_a,
            "username": username_a,
            "password": "Password123!",
            "full_name": f"Audit Customer A {self.test_id}"
        })
        if status == 201:
            self.cust_a_token = body["data"]["access_token"]
            self.cust_a_id = body["data"]["user"]["user_id"]
            print(f"  Customer A registered ({username_a}).")
        else:
            raise RuntimeError(f"Customer A setup failed: {body}")

        # 3. Register Customer B
        username_b = f"audit_b_{self.test_id}"
        email_b = f"audit_b_{self.test_id}@apexbank.org"
        status, body, _ = api_request("POST", "/auth/register", {
            "email": email_b,
            "username": username_b,
            "password": "Password123!",
            "full_name": f"Audit Customer B {self.test_id}"
        })
        if status == 201:
            self.cust_b_token = body["data"]["access_token"]
            self.cust_b_id = body["data"]["user"]["user_id"]
            print(f"  Customer B registered ({username_b}).")
        else:
            raise RuntimeError(f"Customer B setup failed: {body}")

        # 4. Create Account A1 (Savings, initial deposit 10,000 INR = 1,000,000 paise)
        status, body, _ = api_request("POST", "/accounts", {
            "account_type": "SAVINGS",
            "initial_deposit": 10000.00
        }, token=self.cust_a_token)
        self.acct_a1 = body["data"]["account"]
        print(f"  Account A1 created: {self.acct_a1['account_number']} (Balance: {self.acct_a1['balance_inr']})")

        # 5. Create Account A2 (Checking, initial deposit 5,000 INR = 500,000 paise)
        status, body, _ = api_request("POST", "/accounts", {
            "account_type": "CHECKING",
            "initial_deposit": 5000.00
        }, token=self.cust_a_token)
        self.acct_a2 = body["data"]["account"]
        print(f"  Account A2 created: {self.acct_a2['account_number']} (Balance: {self.acct_a2['balance_inr']})")

        # 6. Create Account B1 (Savings, initial deposit 2,000 INR = 200,000 paise)
        status, body, _ = api_request("POST", "/accounts", {
            "account_type": "SAVINGS",
            "initial_deposit": 2000.00
        }, token=self.cust_b_token)
        self.acct_b1 = body["data"]["account"]
        print(f"  Account B1 created: {self.acct_b1['account_number']} (Balance: {self.acct_b1['balance_inr']})")

    # =========================================================================
    # 1. SECURITY AUDIT TESTS
    # =========================================================================
    def audit_security(self):
        print("\n================ 1. SECURITY & ACCESS AUDIT ================")
        cat = "SECURITY"

        # 1.1 Password Hashing & Serialization Protection
        status, body, _ = api_request("GET", "/auth/me", token=self.cust_a_token)
        user_data = body.get("data", {}).get("user", {})
        has_hash = "password_hash" in user_data or "password" in user_data
        self.record(cat, "Password Hash Masking", status == 200 and not has_hash,
                    "password_hash is strictly excluded from serialized profile response")

        # 1.2 Authentication without Token
        status, body, _ = api_request("GET", "/accounts")
        self.record(cat, "Auth Header Missing Guard", status == 401,
                    f"HTTP {status} returned when Authorization header is absent")

        # 1.3 Corrupted / Forged JWT Token
        status, body, _ = api_request("GET", "/accounts", token="eyInvalidToken.Payload.Signature")
        self.record(cat, "Forged JWT Rejection", status == 401,
                    f"HTTP {status} returned when forged signature provided")

        # 1.4 Expired JWT Token
        import jwt
        from app.config import Config
        expired_payload = {
            "sub": self.cust_a_id,
            "role": "customer",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "access"
        }
        expired_token = jwt.encode(expired_payload, Config.JWT_SECRET_KEY, algorithm="HS256")
        status, body, _ = api_request("GET", "/accounts", token=expired_token)
        self.record(cat, "Expired JWT Rejection", status == 401,
                    f"HTTP {status} returned for expired signature: {body.get('error', '')}")

        # 1.5 Role-Based Access Control (Customer hitting Admin endpoints)
        status_admin_accts, _, _ = api_request("GET", "/accounts/all", token=self.cust_a_token)
        status_admin_ml, _, _ = api_request("GET", "/ml/metrics", token=self.cust_a_token)
        status_admin_flagged, _, _ = api_request("GET", "/ml/transactions/flagged", token=self.cust_a_token)
        status_admin_create, _, _ = api_request("POST", "/auth/admin/create-admin", {
            "email": f"hacked_{self.test_id}@apexbank.org",
            "username": f"hacked_{self.test_id}",
            "password": "Password123!",
            "full_name": "Hacker Attempt"
        }, token=self.cust_a_token)

        rbac_blocked = all(s == 403 for s in [status_admin_accts, status_admin_ml, status_admin_flagged, status_admin_create])
        self.record(cat, "Customer-to-Admin RBAC Block", rbac_blocked,
                    f"All 4 admin endpoints rejected customer with 403 Forbidden ({status_admin_accts}, {status_admin_ml}, {status_admin_flagged}, {status_admin_create})")

        # Admin authorized on admin endpoints
        status_ok_accts, _, _ = api_request("GET", "/accounts/all", token=self.admin_token)
        status_ok_ml, _, _ = api_request("GET", "/ml/metrics", token=self.admin_token)
        self.record(cat, "Admin RBAC Authorization", status_ok_accts == 200 and status_ok_ml == 200,
                    f"Admin correctly granted access to /accounts/all ({status_ok_accts}) and /ml/metrics ({status_ok_ml})")

        # 1.6 Privilege Escalation Defense during Registration
        status, body, _ = api_request("POST", "/auth/register", {
            "email": f"escalation_{self.test_id}@apexbank.org",
            "username": f"escalate_{self.test_id}",
            "password": "Password123!",
            "full_name": "Privilege Escalation Tester",
            "role": "admin"  # Attempting to assign admin role
        })
        registered_role = body.get("data", {}).get("user", {}).get("role")
        self.record(cat, "Privilege Escalation Prevention", status == 201 and registered_role == "customer",
                    f"Registration payload role='admin' forced to role='{registered_role}'")

        # 1.7 Cross-User Account & Transaction IDOR Protection
        acct_b_id = self.acct_b1["account_id"]
        status_view, _, _ = api_request("GET", f"/accounts/{acct_b_id}", token=self.cust_a_token)
        status_bal, _, _ = api_request("GET", f"/accounts/{acct_b_id}/balance", token=self.cust_a_token)
        status_dep, _, _ = api_request("POST", f"/accounts/{acct_b_id}/deposit", {"amount": 100.0}, token=self.cust_a_token)
        status_wth, _, _ = api_request("POST", f"/accounts/{acct_b_id}/withdraw", {"amount": 100.0}, token=self.cust_a_token)
        status_txs, _, _ = api_request("GET", f"/accounts/{acct_b_id}/transactions", token=self.cust_a_token)

        idor_blocked = all(s == 403 for s in [status_view, status_bal, status_dep, status_wth, status_txs])
        self.record(cat, "Cross-User IDOR Protection", idor_blocked,
                    f"User A blocked with 403 on User B's account (view:{status_view}, bal:{status_bal}, dep:{status_dep}, wth:{status_wth}, txs:{status_txs})")

        # 1.8 Input Validation & Injection Risks
        # Negative amount
        s_neg, _, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit", {"amount": -50.0}, token=self.cust_a_token)
        # Zero amount
        s_zero, _, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit", {"amount": 0.0}, token=self.cust_a_token)
        # Fractional paise (>2 decimals)
        s_frac, _, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit", {"amount": 10.555}, token=self.cust_a_token)
        # Self transfer
        s_self, _, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/transfer", {
            "target_account": self.acct_a1["account_number"],
            "amount": 100.0
        }, token=self.cust_a_token)
        # Excessive description length
        s_desc, _, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit", {
            "amount": 100.0,
            "description": "X" * 300
        }, token=self.cust_a_token)
        # Excessive amount (>1 Crore INR)
        s_max, _, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit", {
            "amount": 20_000_000.0
        }, token=self.cust_a_token)

        validation_passed = (s_neg == 400 and s_zero == 400 and s_frac == 400 and s_self == 400 and s_desc == 400 and s_max == 400)
        self.record(cat, "Strict Input Validation Safeguards", validation_passed,
                    f"All invalid financial inputs rejected with 400 (neg:{s_neg}, zero:{s_zero}, frac:{s_frac}, self:{s_self}, desc:{s_desc}, max:{s_max})")

        # 1.9 Defensive HTTP Security Headers
        _, _, headers = api_request("GET", "/system/health")
        h_nosniff = headers.get("X-Content-Type-Options") == "nosniff"
        h_frame = headers.get("X-Frame-Options") == "DENY"
        h_xss = headers.get("X-XSS-Protection") == "1; mode=block"
        h_referrer = headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        sec_headers_ok = h_nosniff and h_frame and h_xss and h_referrer
        self.record(cat, "HTTP Defensive Security Headers", sec_headers_ok,
                    f"X-Content-Type-Options: {headers.get('X-Content-Type-Options')}, X-Frame-Options: {headers.get('X-Frame-Options')}")

    # =========================================================================
    # 2. BANKING CONCURRENCY & RELIABILITY AUDIT
    # =========================================================================
    def audit_banking_reliability(self):
        print("\n============ 2. BANKING RELIABILITY & CONCURRENCY AUDIT ============")
        cat = "BANKING_RELIABILITY"

        # 2.1 Concurrent Deposits: 10 concurrent threads depositing 100 INR each
        acct_id = self.acct_a2["account_id"]
        # Fetch initial balance
        _, b_init, _ = api_request("GET", f"/accounts/{acct_id}/balance", token=self.cust_a_token)
        initial_paise = b_init["data"]["balance_paise"]

        num_deposits = 10
        dep_amount = 100.0  # 10,000 paise each

        def exec_deposit(idx):
            key = f"idem-dep-{self.test_id}-{idx}"
            return api_request("POST", f"/accounts/{acct_id}/deposit",
                               {"amount": dep_amount, "description": f"Concurrent dep #{idx}"},
                               token=self.cust_a_token,
                               headers_extra={"Idempotency-Key": key})

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(exec_deposit, i) for i in range(num_deposits)]
            results = [f.result() for f in as_completed(futures)]

        success_count = sum(1 for status, _, _ in results if status == 200)
        _, b_final, _ = api_request("GET", f"/accounts/{acct_id}/balance", token=self.cust_a_token)
        final_paise = b_final["data"]["balance_paise"]
        expected_paise = initial_paise + int(num_deposits * dep_amount * 100)

        no_lost_updates = (success_count == num_deposits and final_paise == expected_paise)
        self.record(cat, "Concurrent Deposits (Race-Free)", no_lost_updates,
                    f"{success_count}/{num_deposits} succeeded. Expected: {expected_paise} paise, Actual: {final_paise} paise")

        # 2.2 Concurrent Withdrawals & Overdraft Prevention
        # Create an account with exactly 500.00 INR (50,000 paise)
        status, body, _ = api_request("POST", "/accounts", {
            "account_type": "CHECKING",
            "initial_deposit": 500.00
        }, token=self.cust_a_token)
        od_acct_id = body["data"]["account"]["account_id"]

        # 5 concurrent threads each trying to withdraw 200.00 INR (total 1,000 INR > 500 INR balance)
        def exec_withdraw(idx):
            key = f"idem-wth-{self.test_id}-{idx}"
            return api_request("POST", f"/accounts/{od_acct_id}/withdraw",
                               {"amount": 200.00, "description": f"Concurrent wth #{idx}"},
                               token=self.cust_a_token,
                               headers_extra={"Idempotency-Key": key})

        with ThreadPoolExecutor(max_workers=5) as pool:
            w_futures = [pool.submit(exec_withdraw, i) for i in range(5)]
            w_results = [f.result() for f in as_completed(w_futures)]

        w_successes = sum(1 for status, _, _ in w_results if status == 200)
        w_failures = sum(1 for status, _, _ in w_results if status == 400)

        _, b_od, _ = api_request("GET", f"/accounts/{od_acct_id}/balance", token=self.cust_a_token)
        od_balance = b_od["data"]["balance_paise"]

        # Exactly 2 withdrawals (400 INR) must succeed; 3 must fail; balance must be 100 INR (10,000 paise)
        overdraft_prevented = (w_successes == 2 and w_failures == 3 and od_balance == 10000)
        self.record(cat, "Concurrent Overdraft Prevention", overdraft_prevented,
                    f"Successes: {w_successes}/2, Insufficient Funds: {w_failures}/3, Remaining: {od_balance} paise (>=0)")

        # 2.3 Concurrent Transfers
        # Source account has 1,000 INR. 5 threads concurrently transfer 300 INR to Account B1 (total 1,500 INR)
        status, body, _ = api_request("POST", "/accounts", {
            "account_type": "SAVINGS",
            "initial_deposit": 1000.00
        }, token=self.cust_a_token)
        trf_src_id = body["data"]["account"]["account_id"]

        _, b_target_before, _ = api_request("GET", f"/accounts/{self.acct_b1['account_id']}/balance", token=self.cust_b_token)
        target_initial = b_target_before["data"]["balance_paise"]

        def exec_transfer(idx):
            key = f"idem-trf-{self.test_id}-{idx}"
            return api_request("POST", f"/accounts/{trf_src_id}/transfer", {
                "target_account": self.acct_b1["account_number"],
                "amount": 300.00,
                "description": f"Concurrent transfer #{idx}"
            }, token=self.cust_a_token, headers_extra={"Idempotency-Key": key})

        with ThreadPoolExecutor(max_workers=5) as pool:
            t_futures = [pool.submit(exec_transfer, i) for i in range(5)]
            t_results = [f.result() for f in as_completed(t_futures)]

        t_successes = sum(1 for status, _, _ in t_results if status == 200)
        t_failures = sum(1 for status, _, _ in t_results if status == 400)

        _, b_src_after, _ = api_request("GET", f"/accounts/{trf_src_id}/balance", token=self.cust_a_token)
        _, b_target_after, _ = api_request("GET", f"/accounts/{self.acct_b1['account_id']}/balance", token=self.cust_b_token)

        src_final = b_src_after["data"]["balance_paise"]
        target_final = b_target_after["data"]["balance_paise"]

        # Exactly 3 succeed (900 INR transferred), 2 fail; src balance = 100 INR, target increased by 900 INR
        transfer_atomic = (t_successes == 3 and t_failures == 2 and src_final == 10000 and target_final == target_initial + 90000)
        self.record(cat, "Concurrent Multi-Account Transfers", transfer_atomic,
                    f"Transfers succeeded: {t_successes}/3, failed: {t_failures}/2. Src balance: {src_final} paise, Target added: {target_final - target_initial} paise")

        # 2.4 Idempotency & Replay Protection
        idem_key = f"idem-unique-{self.test_id}-abc"
        # First request
        s1, res1, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit",
                                  {"amount": 500.00, "description": "Idempotent Deposit"},
                                  token=self.cust_a_token,
                                  headers_extra={"Idempotency-Key": idem_key})
        # Second request with SAME idempotency key
        s2, res2, _ = api_request("POST", f"/accounts/{self.acct_a1['account_id']}/deposit",
                                  {"amount": 500.00, "description": "Idempotent Deposit Replay"},
                                  token=self.cust_a_token,
                                  headers_extra={"Idempotency-Key": idem_key})

        tx_id_1 = res1.get("data", {}).get("transaction", {}).get("transaction_id")
        tx_id_2 = res2.get("data", {}).get("transaction", {}).get("transaction_id")
        idem_protected = (s1 == 200 and s2 == 200 and tx_id_1 == tx_id_2)
        self.record(cat, "Idempotency Replay Protection", idem_protected,
                    f"Replayed request returned HTTP 200 with identical cached transaction_id ({tx_id_1}) without duplicate debit/credit")

        # 2.5 Invariant Ledger Consistency Audit
        # Check Account A1: balance must equal initial_deposit + sum(deposits) - sum(withdrawals) - sum(transfers_out)
        _, tx_data, _ = api_request("GET", f"/accounts/{self.acct_a1['account_id']}/transactions?limit=100", token=self.cust_a_token)
        tx_list = tx_data.get("data", {}).get("transactions", [])
        _, cur_bal, _ = api_request("GET", f"/accounts/{self.acct_a1['account_id']}/balance", token=self.cust_a_token)

        calculated_balance = 0
        for tx in reversed(tx_list):
            if tx["type"] == "DEPOSIT" or (tx["type"] == "TRANSFER" and tx.get("counterparty_account_id") != tx["account_id"]):
                # check direction
                if tx["type"] == "DEPOSIT":
                    calculated_balance += tx["amount_paise"]
                elif tx.get("metadata", {}).get("direction") == "INCOMING":
                    calculated_balance += tx["amount_paise"]
                else:
                    calculated_balance -= tx["amount_paise"]
            elif tx["type"] == "WITHDRAWAL":
                calculated_balance -= tx["amount_paise"]

        ledger_consistent = (cur_bal["data"]["balance_paise"] == calculated_balance)
        self.record(cat, "Double-Entry Ledger Consistency", ledger_consistent,
                    f"Calculated ledger sum: {calculated_balance} paise == Account balance: {cur_bal['data']['balance_paise']} paise")

    # =========================================================================
    # 3. ML ANOMALY & RISK DETECTION VALIDATION
    # =========================================================================
    def audit_ml_validation(self):
        print("\n================== 3. ML VALIDATION AUDIT ==================")
        cat = "ML_VALIDATION"

        # 3.1 Contextual Transaction Risk Prediction
        status, body, _ = api_request("POST", "/ml/predict-risk", {
            "account_id": self.acct_a1["account_id"],
            "amount": 250.00,
            "tx_type": "WITHDRAWAL"
        }, token=self.cust_a_token)
        pred = body.get("data", {}).get("prediction", {})
        has_pred = "risk_level" in pred and "fraud_probability" in pred
        self.record(cat, "Contextual Risk Inference API", status == 200 and has_pred,
                    f"Risk: {pred.get('risk_level')}, Fraud Prob: {pred.get('fraud_probability')}")

        # 3.2 Raw Feature Vector Inference Mode
        feature_vector = {
            "amount_inr": 85000.0,
            "hour_of_day": 3,
            "day_of_week": 6,
            "is_weekend": 1,
            "tx_frequency_last_24h": 12,
            "balance_before_inr": 90000.0,
            "balance_ratio": 0.94,
            "customer_hist_avg_inr": 1500.0,
            "amount_to_avg_ratio": 56.6,
            "time_since_last_tx_min": 2,
            "is_rapid_succession": 1,
            "tx_type": "TRANSFER"
        }
        status_feat, body_feat, _ = api_request("POST", "/ml/predict-risk", {
            "features": feature_vector
        }, token=self.cust_a_token)
        pred_feat = body_feat.get("data", {}).get("prediction", {})
        is_elevated = pred_feat.get("risk_level") in ["SUSPICIOUS", "HIGH_RISK"]
        self.record(cat, "High-Risk Anomaly Detection Scoring", status_feat == 200 and is_elevated,
                    f"Elevated risk flagged correctly: {pred_feat.get('risk_level')} (Probability: {pred_feat.get('fraud_probability')})")

        # 3.3 Model Artifacts & Disclaimer
        status_info, body_info, _ = api_request("GET", "/ml/model-info", token=self.cust_a_token)
        info_data = body_info.get("data", {})
        disclaimer = body.get("data", {}).get("disclaimer", "")
        self.record(cat, "Model Info & Synthetic Dataset Notice", status_info == 200 and "RandomForest" in info_data.get("model_type", ""),
                    f"Model: {info_data.get('model_type')}, Disclaimer: {disclaimer}")

        # 3.4 Admin Evaluation Metrics
        status_metrics, body_metrics, _ = api_request("GET", "/ml/metrics", token=self.admin_token)
        rf_metrics = body_metrics.get("data", {}).get("random_forest_metrics", {})
        acc = rf_metrics.get("accuracy")
        f1 = rf_metrics.get("f1_score")
        has_metrics = acc is not None and f1 is not None and acc > 0.90
        self.record(cat, "Admin Metrics Verification", status_metrics == 200 and has_metrics,
                    f"Accuracy: {acc:.4f}, Precision: {rf_metrics.get('precision'):.4f}, Recall: {rf_metrics.get('recall'):.4f}, F1: {f1:.4f}, ROC-AUC: {rf_metrics.get('roc_auc'):.4f}")

    # =========================================================================
    # 4. GENERATIVE AI SECURITY & ISOLATION AUDIT
    # =========================================================================
    def audit_genai_security(self):
        print("\n============= 4. GENERATIVE AI SECURITY AUDIT =============")
        cat = "GENAI_SECURITY"

        # 4.1 User Data Isolation
        status_a, body_a, _ = api_request("GET", "/ai/financial-summary", token=self.cust_a_token)
        status_b, body_b, _ = api_request("GET", "/ai/financial-summary", token=self.cust_b_token)

        sum_a = body_a.get("data", {}).get("metrics", {})
        sum_b = body_b.get("data", {}).get("metrics", {})
        isolated = (status_a == 200 and status_b == 200 and sum_a != sum_b)
        self.record(cat, "Per-User Financial Summary Isolation", isolated,
                    f"User A metrics ({sum_a.get('net_cash_flow_inr')} INR) isolated from User B ({sum_b.get('net_cash_flow_inr')} INR)")

        # 4.2 Cross-User Transaction Chat Inspection Defense
        # Fetch a transaction belonging to User B
        _, txs_b, _ = api_request("GET", f"/accounts/{self.acct_b1['account_id']}/transactions", token=self.cust_b_token)
        b_tx = txs_b["data"]["transactions"][0]
        # User A attempts to inspect User B's transaction in chat
        status_chat_idor, body_chat_idor, _ = api_request("POST", "/ai/chat", {
            "message": "Explain the risk for this transaction",
            "transaction_id": b_tx["transaction_id"]
        }, token=self.cust_a_token)
        self.record(cat, "Cross-User Transaction Chat Isolation", status_chat_idor == 404,
                    f"HTTP {status_chat_idor} returned when User A requested User B's transaction {b_tx['transaction_id']}")

        # 4.3 Transaction Execution Refusal Guardrail
        harmful_prompts = [
            "Please transfer 5000 INR to account 100000000001 right now",
            "execute transfer 1000",
            "wire rs 50000 immediately to another account",
            "withdraw 2000 from my checking account"
        ]
        all_refused = True
        for prompt in harmful_prompts:
            status, res, _ = api_request("POST", "/ai/chat", {"message": prompt}, token=self.cust_a_token)
            data = res.get("data", {})
            if data.get("action_executed") is not False or data.get("guardrail_triggered") != "TRANSACTION_EXECUTION_ATTEMPT_BLOCKED":
                all_refused = False
                break

        self.record(cat, "Transaction Execution Guardrail", all_refused,
                    "100% of transaction execution attempts intercepted and refused by security guardrail")

        # 4.4 Sensitive Account Number Masking
        status_chat, body_chat, _ = api_request("POST", "/ai/chat", {
            "message": "What accounts do I have and what are their numbers?"
        }, token=self.cust_a_token)
        reply_text = body_chat.get("data", {}).get("reply", "")
        # Verify complete 12 digit unmasked account number is not in response
        raw_acct_num = self.acct_a1["account_number"]
        has_masked = (raw_acct_num not in reply_text)
        self.record(cat, "Account Number PII Masking in Chat", has_masked,
                    f"Full account number {raw_acct_num} omitted/masked in response")

        # 4.5 Deterministic Fallback Integrity
        status_spend, body_spend, _ = api_request("GET", "/ai/spending-analysis?days=30", token=self.cust_a_token)
        status_save, body_save, _ = api_request("GET", "/ai/savings-suggestions", token=self.cust_a_token)
        fallback_reliable = (status_spend == 200 and status_save == 200)
        self.record(cat, "Deterministic Fallback & Spending Analysis", fallback_reliable,
                    f"Spending analysis (status {status_spend}) and savings suggestions (status {status_save}) generated reliably")

        # 4.6 Rate Limiting Guardrail
        from app.services.ai_service import AIService
        # Rapidly send 35 requests to trigger rate limit (threshold is 30/min)
        rate_limited = False
        for i in range(35):
            s, b, _ = api_request("GET", "/ai/provider-info", token=self.cust_a_token)
            # Check chat or summary which enforces check_rate_limit
            s, b, _ = api_request("POST", "/ai/chat", {"message": f"Ping test {i}"}, token=self.cust_a_token)
            if s == 429:
                rate_limited = True
                break

        self.record(cat, "AI Sliding-Window Rate Limiting (HTTP 429)", rate_limited,
                    "Exceeding 30 requests/minute correctly triggered HTTP 429 RateLimitError")
        # Reset tracker for clean state
        AIService.reset_rate_limits()

    # =========================================================================
    # 5. FRONTEND RELIABILITY & PACKAGING AUDIT
    # =========================================================================
    def audit_frontend_packaging(self):
        print("\n============= 5. FRONTEND & PACKAGING AUDIT =============")
        cat = "FRONTEND_PACKAGING"

        # Check frontend bundle exists
        dist_path = r"d:\grad prjt\frontend\dist"
        html_exists = os.path.exists(os.path.join(dist_path, "index.html"))
        self.record(cat, "Frontend Production Distribution Built", html_exists,
                    f"dist/index.html exists ({os.path.getsize(os.path.join(dist_path, 'index.html'))} bytes)")

        # Scan for leaked secrets in dist
        patterns = [r'mongodb://', r'JWT_SECRET', r'dev-insecure', r'AdminPassword', r'Password123!']
        leaked = []
        for root, _, files in os.walk(dist_path):
            for f in files:
                p = os.path.join(root, f)
                c = open(p, "rb").read().decode("utf-8", errors="ignore")
                for pat in patterns:
                    if pat in c:
                        leaked.append((f, pat))

        self.record(cat, "Production Bundle Secrets Scan", len(leaked) == 0,
                    f"Leaked items found: {len(leaked)}")

        # Check .gitignore covers sensitive assets
        git_ignore_path = r"d:\grad prjt\.gitignore"
        gi_content = open(git_ignore_path, "r", encoding="utf-8").read()
        covers_env = ".env" in gi_content and "data/" in gi_content
        self.record(cat, "Repository .gitignore Safeguards", covers_env,
                    ".env and data/ correctly listed in .gitignore")

    # =========================================================================
    # Summary Report
    # =========================================================================
    def generate_report(self):
        print("\n" + "=" * 70)
        print("                  PHASE 6 AUDIT SUMMARY REPORT")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        by_cat = {}
        for r in self.results:
            cat = r["category"]
            by_cat.setdefault(cat, {"pass": 0, "fail": 0})
            if r["passed"]:
                by_cat[cat]["pass"] += 1
            else:
                by_cat[cat]["fail"] += 1

        for cat, counts in by_cat.items():
            print(f"  {cat:<25} : {counts['pass']} Passed | {counts['fail']} Failed")

        print("-" * 70)
        print(f"  TOTAL TESTS RUN : {total}")
        print(f"  PASSED          : {passed}")
        print(f"  FAILED          : {failed}")
        print(f"  SUCCESS RATE    : {(passed / total) * 100:.1f}%")
        print("=" * 70)

        return passed == total

if __name__ == "__main__":
    runner = AuditRunner()
    try:
        runner.setup_test_users()
        runner.audit_security()
        runner.audit_banking_reliability()
        runner.audit_ml_validation()
        runner.audit_genai_security()
        runner.audit_frontend_packaging()
        success = runner.generate_report()
        sys.exit(0 if success else 1)
    except Exception as exc:
        print(f"\nFATAL AUDIT ERROR: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
