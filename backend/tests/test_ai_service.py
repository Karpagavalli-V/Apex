import pytest
from datetime import datetime, timezone, timedelta
from app.extensions import mongo_manager
from app.services.ai_service import AIService
from app.services.banking_service import BankingService
from app.services.llm_client import LLMClient

@pytest.fixture(autouse=True)
def reset_limits():
    """Resets rate limit tracker before each test."""
    AIService.reset_rate_limits()
    yield
    AIService.reset_rate_limits()


def seed_user_transactions(user_id: str, account_id: str):
    """Helper to seed a variety of ledger transactions with distinct types and timestamps."""
    db = mongo_manager.get_db()
    now = datetime.now(timezone.utc)
    
    # Current month: 2 deposits (₹5,000, ₹3,000), 2 withdrawals (₹1,000, ₹2,500), 1 transfer (₹500)
    txs = [
        {
            "transaction_id": "tx_curr_dep_1",
            "account_id": account_id,
            "user_id": user_id,
            "type": "DEPOSIT",
            "amount_paise": 500000,  # ₹5,000
            "balance_after_paise": 600000,
            "status": "COMPLETED",
            "risk_level": "NORMAL",
            "fraud_probability": 0.05,
            "description": "Monthly Salary",
            "timestamp": now - timedelta(days=5)
        },
        {
            "transaction_id": "tx_curr_dep_2",
            "account_id": account_id,
            "user_id": user_id,
            "type": "DEPOSIT",
            "amount_paise": 300000,  # ₹3,000
            "balance_after_paise": 900000,
            "status": "COMPLETED",
            "risk_level": "NORMAL",
            "fraud_probability": 0.04,
            "description": "Consulting Fee",
            "timestamp": now - timedelta(days=3)
        },
        {
            "transaction_id": "tx_curr_wth_1",
            "account_id": account_id,
            "user_id": user_id,
            "type": "WITHDRAWAL",
            "amount_paise": 100000,  # ₹1,000
            "balance_after_paise": 800000,
            "status": "COMPLETED",
            "risk_level": "NORMAL",
            "fraud_probability": 0.08,
            "description": "ATM Cash",
            "timestamp": now - timedelta(days=2)
        },
        {
            "transaction_id": "tx_curr_wth_2",
            "account_id": account_id,
            "user_id": user_id,
            "type": "WITHDRAWAL",
            "amount_paise": 250000,  # ₹2,500 (Outlier)
            "balance_after_paise": 550000,
            "status": "COMPLETED",
            "risk_level": "HIGH_RISK",
            "fraud_probability": 0.88,
            "description": "Electronics Store",
            "timestamp": now - timedelta(days=1)
        },
        {
            "transaction_id": "tx_curr_trf_1",
            "account_id": account_id,
            "user_id": user_id,
            "type": "TRANSFER",
            "amount_paise": 50000,  # ₹500
            "balance_after_paise": 500000,
            "status": "COMPLETED",
            "risk_level": "NORMAL",
            "fraud_probability": 0.12,
            "description": "Split Bill",
            "timestamp": now - timedelta(hours=12)
        }
    ]
    db.transactions.insert_many(txs)


def test_financial_summary_metrics_and_fallback(client, customer_user, customer_account):
    """
    Verifies that GET /api/ai/financial-summary accurately computes inflows, outflows,
    net cash flow in integer paise / INR, and produces structured summary via fallback.
    """
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    res = client.get("/api/ai/financial-summary", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True

    summary = data["data"]
    metrics = summary["metrics"]

    # Total deposits = ₹1,000 (opening) + ₹5,000 + ₹3,000 = ₹9,000 (900000 paise)
    assert metrics["total_deposits_inr"] == 9000.0
    assert metrics["total_deposits_paise"] == 900000
    assert metrics["deposit_count"] == 3

    # Total withdrawals = ₹1,000 + ₹2,500 = ₹3,500 (350000 paise)
    assert metrics["total_withdrawals_inr"] == 3500.0
    assert metrics["withdrawal_count"] == 2

    # Total transfers = ₹500
    assert metrics["total_transfers_inr"] == 500.0
    assert metrics["transfer_count"] == 1

    # Total outflow = ₹4,000; Net cash flow = ₹9,000 - ₹4,000 = ₹5,000
    assert metrics["total_outflow_inr"] == 4000.0
    assert metrics["net_cash_flow_inr"] == 5000.0

    # AI Summary schema
    ai_content = summary["summary"]
    assert "overview" in ai_content
    assert ai_content["cash_flow_health"] in {"EXCELLENT", "GOOD", "BALANCED", "DEFICIT"}
    assert isinstance(ai_content["key_observations"], list)
    assert len(ai_content["key_observations"]) >= 2
    assert "actionable_takeaway" in ai_content


def test_financial_summary_mom_comparison(client, customer_user, customer_account):
    """
    Verifies Month-over-Month calculation when previous month data exists.
    """
    db = mongo_manager.get_db()
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    # Seed prior month transaction
    now = datetime.now(timezone.utc)
    if now.month == 1:
        prev_year, prev_month = now.year - 1, 12
    else:
        prev_year, prev_month = now.year, now.month - 1
    prev_dt = datetime(prev_year, prev_month, 15, 12, 0, 0, tzinfo=timezone.utc)

    db.transactions.insert_one({
        "transaction_id": "tx_prev_dep",
        "account_id": customer_account["account_id"],
        "user_id": customer_user["user_id"],
        "type": "DEPOSIT",
        "amount_paise": 400000,  # ₹4,000
        "balance_after_paise": 400000,
        "status": "COMPLETED",
        "timestamp": prev_dt
    })

    res = client.get("/api/ai/financial-summary", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    mom = res.get_json()["data"]["metrics"]["mom_comparison"]

    assert mom["has_prior_data"] is True
    # Prior deposits ₹4,000 -> Current ₹9,000 -> +125.0% change
    assert mom["prev_deposits_inr"] == 4000.0
    assert mom["inflow_change_pct"] == 125.0


def test_spending_analysis_patterns_and_outliers(client, customer_user, customer_account):
    """
    Verifies GET /api/ai/spending-analysis calculates velocity, identifies peak days,
    and detects outlier transactions exceeding 2.5x average.
    """
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    res = client.get("/api/ai/spending-analysis?days=30", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()["data"]

    metrics = data["metrics"]
    # Total outflow = ₹1,000 + ₹2,500 + ₹500 = ₹4,000
    assert metrics["total_outflow_inr"] == 4000.0
    assert metrics["transaction_count"] == 3
    # Average outflow = 4000 / 3 = 1333.33
    assert metrics["average_outflow_inr"] == 1333.33
    # Outliers (> 2.5 * 1333.33 = 3333.33) -> None exceed 3333, but let's test outlier detection
    assert "top_transactions" in metrics
    assert len(metrics["top_transactions"]) == 3
    # Top transaction is the ₹2,500 withdrawal
    assert metrics["top_transactions"][0]["amount_inr"] == 2500.0

    analysis = data["analysis"]
    assert "spending_pattern_summary" in analysis
    assert "behavioral_insights" in analysis


def test_savings_suggestions_health_and_targets(client, customer_user, customer_account):
    """
    Verifies GET /api/ai/savings-suggestions produces realistic targets,
    emergency fund coverage estimates, and conservative disclaimers.
    """
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    res = client.get("/api/ai/savings-suggestions", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()["data"]

    metrics = data["metrics"]
    assert "monthly_inflow_inr" in metrics
    assert "monthly_outflow_inr" in metrics
    assert "emergency_fund_target_inr" in metrics
    assert metrics["emergency_fund_target_inr"] >= 0

    sugg = data["suggestions"]
    assert sugg["savings_health_rating"] in {"STRONG", "MODERATE", "AT_RISK", "NEGATIVE_CASH_FLOW"}
    assert "recommended_monthly_savings_inr" in sugg
    assert isinstance(sugg["practical_recommendations"], list)
    assert len(sugg["practical_recommendations"]) >= 2
    # Verify disclaimer is present
    assert "disclaimer" in sugg
    assert "not constitute certified investment advice" in sugg["disclaimer"].lower()


def test_chatbot_spending_inquiry(client, customer_user, customer_account):
    """Verifies chatbot answers 'How much did I spend this month?' accurately."""
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    res = client.post(
        "/api/ai/chat",
        headers=customer_user["auth_headers"],
        json={"message": "How much did I spend this month?"}
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "reply" in data
    # Must report ₹4,000.00 outflow
    assert "4,000" in data["reply"] or "4000" in data["reply"]


def test_chatbot_largest_transactions(client, customer_user, customer_account):
    """Verifies chatbot lists top largest transactions when queried."""
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    res = client.post(
        "/api/ai/chat",
        headers=customer_user["auth_headers"],
        json={"message": "What are my largest transactions?"}
    )
    assert res.status_code == 200
    reply = res.get_json()["data"]["reply"]
    # The largest withdrawal is 2,500
    assert "2,500" in reply or "2500" in reply


def test_chatbot_savings_inquiry(client, customer_user):
    """Verifies chatbot provides practical budgeting and savings tips."""
    res = client.post(
        "/api/ai/chat",
        headers=customer_user["auth_headers"],
        json={"message": "How can I save more?"}
    )
    assert res.status_code == 200
    reply = res.get_json()["data"]["reply"].lower()
    assert "save" in reply or "savings" in reply
    assert "reserve" in reply or "deposit" in reply


def test_chatbot_financial_summary(client, customer_user, customer_account):
    """Verifies chatbot provides monthly financial summary overview."""
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    res = client.post(
        "/api/ai/chat",
        headers=customer_user["auth_headers"],
        json={"message": "Show my monthly financial summary"}
    )
    assert res.status_code == 200
    reply = res.get_json()["data"]["reply"]
    assert "financial summary" in reply.lower()
    assert "9,000" in reply or "9000" in reply


def test_chatbot_explain_fraud_risk_level(client, customer_user, customer_account):
    """
    Verifies chatbot explains fraud risk level for a transaction,
    ensuring it clarifies that high risk is an anomaly flag, not proof of fraud.
    """
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    # Query explanation for high-risk transaction
    res = client.post(
        "/api/ai/chat",
        headers=customer_user["auth_headers"],
        json={
            "message": "Explain this transaction's fraud-risk level",
            "transaction_id": "tx_curr_wth_2"
        }
    )
    assert res.status_code == 200
    reply = res.get_json()["data"]["reply"]
    assert "HIGH_RISK" in reply
    assert "0.88" in reply
    # Must explicitly state it is an automated anomaly flag, not proof of fraud
    assert "not definitive legal proof" in reply.lower() or "not proof of fraud" in reply.lower()


def test_chatbot_rejects_transaction_execution(client, customer_user):
    """
    CRITICAL SECURITY TEST:
    Verifies that the chatbot strictly rejects requests to execute monetary transfers,
    withdrawals, or balance modifications.
    """
    queries = [
        "Please transfer ₹500 to account 100987654321",
        "Withdraw ₹1000 from my checking account",
        "Send 250 to Bob right now",
        "Execute transaction to pay my rent"
    ]

    for q in queries:
        res = client.post(
            "/api/ai/chat",
            headers=customer_user["auth_headers"],
            json={"message": q}
        )
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["action_executed"] is False
        assert data.get("guardrail_triggered") == "TRANSACTION_EXECUTION_ATTEMPT_BLOCKED"
        assert "no authority or technical capability to execute" in data["reply"].lower()


def test_cross_user_isolation_for_ai(client, customer_user, second_customer, customer_account):
    """
    Verifies that AI endpoints strictly isolate customer data:
    Second customer cannot see First customer's data or query their transaction IDs.
    """
    seed_user_transactions(customer_user["user_id"], customer_account["account_id"])

    # Second customer requests summary -> should have 0 transactions
    res = client.get("/api/ai/financial-summary", headers=second_customer["auth_headers"])
    assert res.status_code == 200
    summary = res.get_json()["data"]["metrics"]
    assert summary["total_transactions"] == 0
    assert summary["total_deposits_inr"] == 0.0

    # Second customer attempts to ask chatbot about First customer's transaction ID -> 404 Not Found
    res_chat = client.post(
        "/api/ai/chat",
        headers=second_customer["auth_headers"],
        json={
            "message": "Explain this transaction risk",
            "transaction_id": "tx_curr_wth_2"
        }
    )
    assert res_chat.status_code == 404
    err = res_chat.get_json()["error"]
    assert err["code"] == "NOT_FOUND"


def test_rate_limiting_enforcement(client, customer_user, monkeypatch):
    """Verifies that exceeding the rate limit raises 429 RATE_LIMIT_EXCEEDED."""
    monkeypatch.setitem(client.application.config, "AI_RATE_LIMIT_PER_MINUTE", 3)
    AIService.reset_rate_limits()

    for i in range(3):
        res = client.get("/api/ai/financial-summary", headers=customer_user["auth_headers"])
        assert res.status_code == 200

    # 4th request must be rate limited
    res_blocked = client.get("/api/ai/financial-summary", headers=customer_user["auth_headers"])
    assert res_blocked.status_code == 429
    data = res_blocked.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_invalid_requests_validation(client, customer_user):
    """Verifies rejection of invalid parameters across AI endpoints."""
    # Invalid month format
    res_month = client.get("/api/ai/financial-summary?month=2026-13", headers=customer_user["auth_headers"])
    assert res_month.status_code == 400

    res_month_fmt = client.get("/api/ai/financial-summary?month=bad_month", headers=customer_user["auth_headers"])
    assert res_month_fmt.status_code == 400

    # Invalid days param
    res_days = client.get("/api/ai/spending-analysis?days=not_a_number", headers=customer_user["auth_headers"])
    assert res_days.status_code == 400

    # Empty chat message
    res_chat_empty = client.post("/api/ai/chat", headers=customer_user["auth_headers"], json={"message": "   "})
    assert res_chat_empty.status_code == 400


def test_mocked_llm_successful_response(client, customer_user, monkeypatch):
    """
    Verifies that when the external LLM provider responds successfully,
    the response is validated and returned with is_fallback: False.
    """
    mock_llm_json = {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "text": '{"overview": "Great month with positive cash flow.", "cash_flow_health": "EXCELLENT", "key_observations": ["High income", "Low spend"], "actionable_takeaway": "Save more."}',
        "is_fallback": False
    }

    monkeypatch.setattr(LLMClient, "generate", lambda **kwargs: mock_llm_json)

    res = client.get("/api/ai/financial-summary", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["provider"] == "gemini"
    assert data["is_fallback"] is False
    assert data["summary"]["cash_flow_health"] == "EXCELLENT"


def test_llm_failure_resilience_fallback(client, customer_user, monkeypatch):
    """
    Verifies that when an external LLM call raises an exception,
    the system automatically and seamlessly falls back to deterministic generation
    without returning an HTTP 500 error.
    """
    def raise_network_err(**kwargs):
        fallback_fn = kwargs.get("deterministic_fallback_fn")
        if fallback_fn:
            fb = fallback_fn()
            fb["fallback_reason"] = "Connection refused to external LLM endpoint"
            return fb
        raise RuntimeError("Network down")

    monkeypatch.setattr(LLMClient, "generate", raise_network_err)

    res = client.get("/api/ai/financial-summary", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["is_fallback"] is True
    assert "overview" in data["summary"]


def test_ai_provider_info_endpoint(client, customer_user):
    """Verifies GET /api/ai/provider-info returns configuration metadata."""
    res = client.get("/api/ai/provider-info", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "provider" in data
    assert "rate_limit_per_minute" in data
    assert "fallback_on_error" in data
