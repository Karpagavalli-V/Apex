import os
import json
import joblib
import pandas as pd
from datetime import datetime, timezone, timedelta
from app.extensions import mongo_manager
from app.utils.logger import logger
from app.utils.errors import AppError, ValidationError

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "artifacts", "fraud_detector.joblib")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "artifacts", "metrics.json")

# Documented Risk Thresholds
THRESHOLD_NORMAL_MAX = 0.25
THRESHOLD_HIGH_RISK_MIN = 0.70

FEATURE_NAMES = [
    "amount_inr",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "tx_frequency_last_24h",
    "balance_before_inr",
    "balance_ratio",
    "customer_hist_avg_inr",
    "amount_to_avg_ratio",
    "time_since_last_tx_min",
    "is_rapid_succession",
    "tx_type"
]

class MLService:
    """
    Service for Machine Learning fraud scoring and real-time transaction risk inference.
    """
    _model = None
    _metrics = None

    @classmethod
    def get_model(cls):
        """Loads and caches the trained Random Forest Pipeline artifact."""
        if cls._model is None:
            if not os.path.exists(MODEL_PATH):
                logger.error(f"ML Model artifact not found at: {MODEL_PATH}")
                raise AppError("Fraud detection model is not loaded or artifact is missing.", status_code=500)
            try:
                cls._model = joblib.load(MODEL_PATH)
                logger.info(f"Loaded ML model from: {MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load ML model artifact: {e}")
                raise AppError(f"Failed to load ML model: {str(e)}", status_code=500)
        return cls._model

    @classmethod
    def get_metrics(cls) -> dict:
        """Loads evaluation metrics and model metadata."""
        if cls._metrics is None:
            if os.path.exists(METRICS_PATH):
                with open(METRICS_PATH, "r") as f:
                    cls._metrics = json.load(f)
            else:
                cls._metrics = {"error": "metrics.json not found"}
        return cls._metrics

    @classmethod
    def classify_risk(cls, fraud_probability: float) -> str:
        """
        Classifies fraud probability into three discrete risk categories:
          - NORMAL     : probability < 0.25
          - SUSPICIOUS : 0.25 <= probability < 0.70
          - HIGH_RISK  : probability >= 0.70
        """
        if fraud_probability < THRESHOLD_NORMAL_MAX:
            return "NORMAL"
        elif fraud_probability < THRESHOLD_HIGH_RISK_MIN:
            return "SUSPICIOUS"
        else:
            return "HIGH_RISK"

    @classmethod
    def extract_features_from_db(
        cls,
        account_id: str,
        user_id: str,
        amount_paise: int,
        tx_type: str,
        tx_time: datetime = None
    ) -> dict:
        """
        Extracts behavioral, temporal, and account balance ratio features
        from MongoDB transaction history for live inference.
        """
        if tx_time is None:
            tx_time = datetime.now(timezone.utc)
        elif tx_time.tzinfo is None:
            tx_time = tx_time.replace(tzinfo=timezone.utc)

        db = mongo_manager.get_db()
        amount_inr = round(amount_paise / 100.0, 2)

        # 1. Current balance before transaction
        balance_before_inr = 0.0
        if db is not None:
            acct = db.accounts.find_one({"account_id": account_id})
            if acct:
                balance_before_inr = round(acct.get("balance_paise", 0) / 100.0, 2)

        # 2. Historical average transaction amount for this customer
        hist_avg_inr = amount_inr
        tx_frequency_last_24h = 1
        time_since_last_tx_min = 1440.0  # default 24h if no previous transaction

        if db is not None:
            # Query recent transactions for account
            since_24h = tx_time - timedelta(hours=24)
            recent_count = db.transactions.count_documents({
                "account_id": account_id,
                "timestamp": {"$gte": since_24h}
            })
            tx_frequency_last_24h = max(1, recent_count + 1)

            # Find previous transaction to compute elapsed time
            last_tx = db.transactions.find_one(
                {"account_id": account_id},
                sort=[("timestamp", -1)]
            )
            if last_tx and last_tx.get("timestamp"):
                last_time = last_tx["timestamp"]
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                diff_sec = max(1.0, (tx_time - last_time).total_seconds())
                time_since_last_tx_min = round(diff_sec / 60.0, 2)

            # Customer average amount across all previous transactions
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": None, "avg_amount": {"$avg": "$amount_paise"}}}
            ]
            agg = list(db.transactions.aggregate(pipeline))
            if agg and agg[0].get("avg_amount"):
                hist_avg_inr = round(float(agg[0]["avg_amount"]) / 100.0, 2)

        # 3. Derived temporal and ratio features
        hour_of_day = tx_time.hour
        day_of_week = tx_time.weekday()
        is_weekend = 1 if day_of_week in [5, 6] else 0
        is_rapid_succession = 1 if time_since_last_tx_min < 5.0 else 0

        balance_ratio = round(amount_inr / (balance_before_inr + 1.0), 4)
        amount_to_avg_ratio = round(amount_inr / (hist_avg_inr + 1.0), 4)

        return {
            "amount_inr": amount_inr,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "tx_frequency_last_24h": tx_frequency_last_24h,
            "balance_before_inr": balance_before_inr,
            "balance_ratio": balance_ratio,
            "customer_hist_avg_inr": hist_avg_inr,
            "amount_to_avg_ratio": amount_to_avg_ratio,
            "time_since_last_tx_min": time_since_last_tx_min,
            "is_rapid_succession": is_rapid_succession,
            "tx_type": tx_type.upper()
        }

    @classmethod
    def predict_risk(cls, features: dict) -> dict:
        """
        Runs real-time inference using the Random Forest pipeline.
        Validates feature vector and outputs probability and discrete risk tier.
        """
        # Validate that required keys are present
        missing_keys = [k for k in FEATURE_NAMES if k not in features]
        if missing_keys:
            raise ValidationError(f"Missing required ML features for scoring: {missing_keys}")

        model = cls.get_model()

        # Build single-row DataFrame aligned with training columns
        input_df = pd.DataFrame([{k: features[k] for k in FEATURE_NAMES}])

        try:
            probabilities = model.predict_proba(input_df)[0]
            # Probability of Class 1 (Fraud)
            fraud_prob = round(float(probabilities[1]), 4)
            normal_prob = round(float(probabilities[0]), 4)
        except Exception as e:
            logger.error(f"Inference error during model.predict_proba: {e}")
            raise AppError(f"Prediction inference failed: {str(e)}", status_code=500)

        risk_level = cls.classify_risk(fraud_prob)

        return {
            "fraud_probability": fraud_prob,
            "normal_probability": normal_prob,
            "risk_level": risk_level,
            "model_version": "1.0.0-rf",
            "thresholds": {
                "normal_max": THRESHOLD_NORMAL_MAX,
                "high_risk_min": THRESHOLD_HIGH_RISK_MIN
            },
            "features_analyzed": features
        }
