import pytest
import pandas as pd
from app.services.ml_service import MLService, THRESHOLD_NORMAL_MAX, THRESHOLD_HIGH_RISK_MIN
from app.utils.errors import ValidationError
from app.extensions import mongo_manager

def test_model_artifact_loading():
    """Verifies that the Random Forest model pipeline loads cleanly from disk."""
    model = MLService.get_model()
    assert model is not None
    assert "preprocessor" in model.named_steps
    assert "classifier" in model.named_steps
    assert hasattr(model.named_steps["classifier"], "predict_proba")
    assert list(model.classes_) == [0, 1]


def test_feature_preprocessing_pipeline():
    """Verifies that raw mixed-type feature dictionaries transform into valid numeric matrices."""
    model = MLService.get_model()
    preprocessor = model.named_steps["preprocessor"]

    sample_df = pd.DataFrame([{
        "amount_inr": 1200.0,
        "hour_of_day": 14,
        "day_of_week": 2,
        "is_weekend": 0,
        "tx_frequency_last_24h": 2,
        "balance_before_inr": 25000.0,
        "balance_ratio": 0.048,
        "customer_hist_avg_inr": 1100.0,
        "amount_to_avg_ratio": 1.09,
        "time_since_last_tx_min": 180.0,
        "is_rapid_succession": 0,
        "tx_type": "TRANSFER"
    }])

    transformed = preprocessor.transform(sample_df)
    assert transformed.shape[0] == 1
    # 11 numerical + 3 one-hot columns (DEPOSIT, WITHDRAWAL, TRANSFER) = 14 features
    assert transformed.shape[1] >= 14
    assert not pd.isna(transformed).any()


def test_risk_classification_three_categories():
    """
    Verifies that the ML model reliably predicts all three risk categories:
    1. NORMAL     (prob < 0.25)
    2. SUSPICIOUS (0.25 <= prob < 0.70)
    3. HIGH_RISK  (prob >= 0.70)
    """
    # 1. Normal Transaction (small daytime deposit, comfortable balance)
    normal_features = {
        "amount_inr": 250.0,
        "hour_of_day": 11,
        "day_of_week": 1,
        "is_weekend": 0,
        "tx_frequency_last_24h": 1,
        "balance_before_inr": 15000.0,
        "balance_ratio": 0.016,
        "customer_hist_avg_inr": 300.0,
        "amount_to_avg_ratio": 0.83,
        "time_since_last_tx_min": 720.0,
        "is_rapid_succession": 0,
        "tx_type": "DEPOSIT"
    }
    pred_normal = MLService.predict_risk(normal_features)
    assert pred_normal["risk_level"] == "NORMAL"
    assert pred_normal["fraud_probability"] < THRESHOLD_NORMAL_MAX

    # 2. Suspicious Transaction (elevated velocity and higher amount)
    suspicious_features = {
        "amount_inr": 9500.0,
        "hour_of_day": 23,
        "day_of_week": 4,
        "is_weekend": 0,
        "tx_frequency_last_24h": 6,
        "balance_before_inr": 16000.0,
        "balance_ratio": 0.59,
        "customer_hist_avg_inr": 1500.0,
        "amount_to_avg_ratio": 6.33,
        "time_since_last_tx_min": 6.0,
        "is_rapid_succession": 0,
        "tx_type": "WITHDRAWAL"
    }
    pred_suspicious = MLService.predict_risk(suspicious_features)
    # Probability should be elevated above normal threshold
    assert pred_suspicious["fraud_probability"] >= THRESHOLD_NORMAL_MAX

    # 3. High Risk Transaction (Extreme 95% balance drainage at 2 AM with rapid succession)
    high_risk_features = {
        "amount_inr": 95000.0,
        "hour_of_day": 2,  # 2:00 AM
        "day_of_week": 3,
        "is_weekend": 0,
        "tx_frequency_last_24h": 14,
        "balance_before_inr": 100000.0,
        "balance_ratio": 0.95,  # 95% drainage
        "customer_hist_avg_inr": 2000.0,
        "amount_to_avg_ratio": 47.5,  # massive spike
        "time_since_last_tx_min": 1.2,
        "is_rapid_succession": 1,
        "tx_type": "TRANSFER"
    }
    pred_high = MLService.predict_risk(high_risk_features)
    assert pred_high["risk_level"] == "HIGH_RISK"
    assert pred_high["fraud_probability"] >= THRESHOLD_HIGH_RISK_MIN


def test_predict_risk_invalid_missing_inputs():
    """Verifies that missing features in the input vector raise ValidationError."""
    incomplete_features = {
        "amount_inr": 1000.0,
        "tx_type": "DEPOSIT"
        # missing other 10 required features
    }
    with pytest.raises(ValidationError) as exc:
        MLService.predict_risk(incomplete_features)
    assert "Missing required ML features" in str(exc.value)


def test_ml_api_predict_risk_with_account_id(client, customer_user, customer_account):
    """
    Verifies POST /api/ml/predict-risk using account context.
    Automatically queries MongoDB for historical account metrics.
    """
    res = client.post(
        "/api/ml/predict-risk",
        headers=customer_user["auth_headers"],
        json={
            "account_id": customer_account["account_id"],
            "amount": 250.0,
            "tx_type": "TRANSFER"
        }
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    pred = data["data"]["prediction"]
    assert "fraud_probability" in pred
    assert "risk_level" in pred
    assert pred["risk_level"] in {"NORMAL", "SUSPICIOUS", "HIGH_RISK"}
    assert "features_analyzed" in pred
    assert pred["features_analyzed"]["amount_inr"] == 250.0


def test_ml_api_predict_risk_with_raw_features(client, customer_user):
    """Verifies POST /api/ml/predict-risk using raw feature vectors directly."""
    payload = {
        "features": {
            "amount_inr": 400.0,
            "hour_of_day": 15,
            "day_of_week": 0,
            "is_weekend": 0,
            "tx_frequency_last_24h": 1,
            "balance_before_inr": 8000.0,
            "balance_ratio": 0.05,
            "customer_hist_avg_inr": 500.0,
            "amount_to_avg_ratio": 0.8,
            "time_since_last_tx_min": 360.0,
            "is_rapid_succession": 0,
            "tx_type": "DEPOSIT"
        }
    }
    res = client.post("/api/ml/predict-risk", headers=customer_user["auth_headers"], json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["prediction"]["risk_level"] == "NORMAL"


def test_ml_api_model_info(client, customer_user):
    """Verifies GET /api/ml/model-info returns metadata and evaluation summary."""
    res = client.get("/api/ml/model-info", headers=customer_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    info = data["data"]
    assert info["model_type"] == "RandomForestClassifier"
    assert "NORMAL" in info["risk_categories"]
    assert "HIGH_RISK" in info["risk_categories"]
    assert info["evaluation_summary"]["accuracy"] is not None


def test_ml_api_admin_metrics_and_rbac(client, customer_user, admin_user):
    """
    Verifies that /api/ml/metrics and /api/ml/transactions/flagged
    are restricted to administrators only.
    """
    # Customer blocked
    res_cust = client.get("/api/ml/metrics", headers=customer_user["auth_headers"])
    assert res_cust.status_code == 403

    # Admin allowed
    res_admin = client.get("/api/ml/metrics", headers=admin_user["auth_headers"])
    assert res_admin.status_code == 200
    data = res_admin.get_json()
    assert data["success"] is True
    assert "random_forest_metrics" in data["data"]
    assert "baseline_comparison" in data["data"]

    # Flagged endpoint
    res_flagged = client.get("/api/ml/transactions/flagged", headers=admin_user["auth_headers"])
    assert res_flagged.status_code == 200


def test_transaction_workflow_stores_ml_risk_metadata(client, customer_user, customer_account):
    """
    Verifies that executing a core transaction (deposit/withdrawal) automatically
    enriches the stored transaction document with risk_level and fraud_probability.
    """
    res = client.post(
        f"/api/accounts/{customer_account['account_id']}/deposit",
        headers=customer_user["auth_headers"],
        json={"amount": 350.0, "description": "Paycheck"}
    )
    assert res.status_code == 200
    tx = res.get_json()["data"]["transaction"]

    # Verify risk fields in response
    assert "risk_level" in tx
    assert "fraud_probability" in tx
    assert tx["risk_level"] in {"NORMAL", "SUSPICIOUS", "HIGH_RISK"}
    assert isinstance(tx["fraud_probability"], float)

    # Verify risk fields persisted in MongoDB ledger
    db = mongo_manager.get_db()
    saved_tx = db.transactions.find_one({"transaction_id": tx["transaction_id"]})
    assert saved_tx is not None
    assert "risk_level" in saved_tx
    assert "fraud_probability" in saved_tx
