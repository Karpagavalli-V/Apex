import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server execution
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve
)

def train_fraud_detection_model():
    """
    Trains, evaluates, and persists the Random Forest fraud detection model.
    Also produces visualizations and metrics comparing against a baseline.
    """
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "data", "synthetic_transactions.csv")
    artifacts_dir = os.path.join(base_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    print("=" * 60)
    print("AI-Enhanced Banking: Phase 3 ML Model Training Pipeline")
    print("=" * 60)

    # 1. Load Dataset
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run generate_dataset.py first.")

    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {df.shape[0]} samples, {df.shape[1]} features.")

    # 2. EDA: Class Imbalance Analysis & Visualization
    fraud_counts = df["is_fraud"].value_counts()
    fraud_pct = df["is_fraud"].value_counts(normalize=True) * 100
    print(f"\nClass Distribution:")
    print(f"  Class 0 (Normal): {fraud_counts[0]} ({fraud_pct[0]:.2f}%)")
    print(f"  Class 1 (Fraud) : {fraud_counts[1]} ({fraud_pct[1]:.2f}%)")

    # Plot Class Distribution
    plt.figure(figsize=(6, 4))
    sns.barplot(x=["Normal (0)", "Fraud (1)"], y=fraud_counts.values, palette=["#2563eb", "#dc2626"])
    plt.title("Transaction Class Distribution (Imbalance Analysis)")
    plt.ylabel("Number of Transactions")
    plt.tight_layout()
    plt.savefig(os.path.join(artifacts_dir, "class_distribution.png"), dpi=200)
    plt.close()

    # 3. Features & Target Definition
    numerical_features = [
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
        "is_rapid_succession"
    ]
    categorical_features = ["tx_type"]
    feature_cols = numerical_features + categorical_features

    X = df[feature_cols]
    y = df["is_fraud"]

    # 4. Stratified Train / Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\nTrain set: {X_train.shape[0]} samples | Test set: {X_test.shape[0]} samples")

    # 5. Preprocessing Pipeline
    num_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, numerical_features),
            ("cat", cat_transformer, categorical_features)
        ]
    )

    # 6. Baseline Model (Weighted Logistic Regression)
    print("\nTraining Baseline Model (Weighted Logistic Regression)...")
    baseline_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000))
    ])
    baseline_pipeline.fit(X_train, y_train)
    y_pred_base = baseline_pipeline.predict(X_test)
    y_proba_base = baseline_pipeline.predict_proba(X_test)[:, 1]

    base_metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred_base)), 4),
        "precision": round(float(precision_score(y_test, y_pred_base, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_base)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred_base)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba_base)), 4)
    }
    print(f"Baseline Results -> Accuracy: {base_metrics['accuracy']}, Recall: {base_metrics['recall']}, F1: {base_metrics['f1_score']}, ROC-AUC: {base_metrics['roc_auc']}")

    # 7. Random Forest Classifier (Primary Model)
    print("\nTraining Primary Model (Balanced Random Forest Classifier)...")
    rf_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    rf_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", rf_clf)
    ])

    rf_pipeline.fit(X_train, y_train)

    # 8. Model Evaluation on Test Set
    y_pred_rf = rf_pipeline.predict(X_test)
    y_proba_rf = rf_pipeline.predict_proba(X_test)[:, 1]

    rf_metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred_rf)), 4),
        "precision": round(float(precision_score(y_test, y_pred_rf, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_rf)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred_rf)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba_rf)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_rf).tolist()
    }

    print("\n" + "=" * 45)
    print("Random Forest Evaluation Metrics (Test Set):")
    print(f"  Accuracy  : {rf_metrics['accuracy']:.4f}")
    print(f"  Precision : {rf_metrics['precision']:.4f}")
    print(f"  Recall    : {rf_metrics['recall']:.4f}  <-- Prioritized Fraud Detection")
    print(f"  F1-Score  : {rf_metrics['f1_score']:.4f}")
    print(f"  ROC-AUC   : {rf_metrics['roc_auc']:.4f}")
    print("=" * 45)
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred_rf, target_names=["Normal", "Fraud"]))

    # 9. Confusion Matrix Visualization
    cm = np.array(rf_metrics["confusion_matrix"])
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Pred Normal", "Pred Fraud"], yticklabels=["Actual Normal", "Actual Fraud"])
    plt.title(f"Confusion Matrix (Recall: {rf_metrics['recall']:.2f})")
    plt.ylabel("Ground Truth")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    plt.savefig(os.path.join(artifacts_dir, "confusion_matrix.png"), dpi=200)
    plt.close()

    # 10. ROC Curve Comparison Visualization
    fpr_rf, tpr_rf, _ = roc_curve(y_test, y_proba_rf)
    fpr_base, tpr_base, _ = roc_curve(y_test, y_proba_base)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr_rf, tpr_rf, label=f"Random Forest (AUC = {rf_metrics['roc_auc']:.3f})", color="#2563eb", lw=2)
    plt.plot(fpr_base, tpr_base, label=f"Baseline Logistic (AUC = {base_metrics['roc_auc']:.3f})", color="#6b7280", lw=2, linestyle="--")
    plt.plot([0, 1], [0, 1], color="black", linestyle=":")
    plt.title("ROC Curves Comparison")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(artifacts_dir, "roc_curve.png"), dpi=200)
    plt.close()

    # 11. Feature Importance Extraction & Visualization
    fitted_preprocessor = rf_pipeline.named_steps["preprocessor"]
    fitted_clf = rf_pipeline.named_steps["classifier"]
    
    cat_encoder = fitted_preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = numerical_features + cat_names
    
    importances = fitted_clf.feature_importances_
    feat_imp_df = pd.DataFrame({
        "feature": all_feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False)

    plt.figure(figsize=(8, 5))
    sns.barplot(data=feat_imp_df, x="importance", y="feature", palette="Blues_r")
    plt.title("Random Forest Feature Importances")
    plt.xlabel("Relative Importance Score")
    plt.ylabel("Features")
    plt.tight_layout()
    plt.savefig(os.path.join(artifacts_dir, "feature_importance.png"), dpi=200)
    plt.close()

    # 12. Save Trained Pipeline & Metrics
    model_artifact_path = os.path.join(artifacts_dir, "fraud_detector.joblib")
    joblib.dump(rf_pipeline, model_artifact_path)
    print(f"\n[SAVED] Pipeline artifact saved to: {model_artifact_path}")

    # Threshold definition
    thresholds = {
        "normal_threshold": 0.25,
        "high_risk_threshold": 0.70,
        "description": "Probability < 0.25 -> NORMAL; 0.25 <= p < 0.70 -> SUSPICIOUS; p >= 0.70 -> HIGH_RISK"
    }

    metrics_payload = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "class_weight": "balanced",
        "trained_at": pd.Timestamp.now().isoformat(),
        "dataset_size": len(df),
        "test_size": len(y_test),
        "baseline_comparison": {
            "model": "Weighted LogisticRegression",
            "metrics": base_metrics
        },
        "random_forest_metrics": rf_metrics,
        "feature_importances": feat_imp_df.to_dict(orient="records"),
        "risk_thresholds": thresholds
    }

    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"[SAVED] Evaluation metrics saved to: {metrics_path}")

    return rf_metrics

if __name__ == "__main__":
    train_fraud_detection_model()
