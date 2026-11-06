import os
import json
import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

def evaluate_saved_model():
    """Evaluates the saved fraud_detector.joblib model against test data."""
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, "artifacts", "fraud_detector.joblib")
    data_path = os.path.join(base_dir, "data", "synthetic_transactions.csv")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    model = joblib.load(model_path)
    df = pd.read_csv(data_path)

    feature_cols = [
        "amount_inr", "hour_of_day", "day_of_week", "is_weekend",
        "tx_frequency_last_24h", "balance_before_inr", "balance_ratio",
        "customer_hist_avg_inr", "amount_to_avg_ratio", "time_since_last_tx_min",
        "is_rapid_succession", "tx_type"
    ]

    X = df[feature_cols]
    y = df["is_fraud"]

    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]

    print("=== Model Evaluation on Full Synthetic Dataset ===")
    print(classification_report(y, y_pred, target_names=["Normal", "Fraud"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y, y_proba):.4f}")

if __name__ == "__main__":
    evaluate_saved_model()
