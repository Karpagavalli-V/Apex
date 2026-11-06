from flask import Blueprint, request, jsonify
from app.utils.auth_guards import jwt_required, roles_required, get_current_user
from app.services.ml_service import MLService
from app.extensions import mongo_manager
from app.models.transaction import Transaction
from app.utils.errors import ValidationError, NotFoundError

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")

@ml_bp.route("/predict-risk", methods=["POST"])
@jwt_required
def predict_transaction_risk():
    """
    Evaluates fraud risk for a proposed or simulated transaction.
    Can accept either raw feature dict OR account_id + amount + tx_type.
    """
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")

    # Mode 1: Contextual scoring from account and amount
    if "account_id" in data and ("amount" in data or "amount_paise" in data):
        account_id = str(data["account_id"]).strip()
        db = mongo_manager.get_db()
        acct = db.accounts.find_one({"account_id": account_id})
        if not acct:
            raise NotFoundError(f"Account '{account_id}' not found")

        # Verify access: customer must own account or be admin
        is_admin = user.get("role") == "admin"
        if not (is_admin or acct["user_id"] == user.get("user_id")):
            raise ValidationError("You do not have permission to evaluate transactions for this account")

        # Parse amount
        from app.utils.validators import parse_amount_to_paise
        amount_paise = parse_amount_to_paise(data, field_name="amount", allow_zero=False)
        tx_type = str(data.get("tx_type", "TRANSFER")).upper()

        features = MLService.extract_features_from_db(
            account_id=account_id,
            user_id=user["user_id"],
            amount_paise=amount_paise,
            tx_type=tx_type
        )
    # Mode 2: Direct raw feature vector scoring
    elif "features" in data and isinstance(data["features"], dict):
        features = data["features"]
    elif "amount_inr" in data and "tx_type" in data:
        features = data
    else:
        raise ValidationError(
            "Payload must contain either ('account_id' and 'amount') or 'features' object with model variables."
        )

    # Perform ML scoring
    prediction = MLService.predict_risk(features)

    return jsonify({
        "success": True,
        "data": {
            "prediction": prediction,
            "disclaimer": "Demonstration ML model for simulated transaction anomaly detection."
        }
    }), 200


@ml_bp.route("/model-info", methods=["GET"])
@jwt_required
def get_model_info():
    """Returns model metadata, feature list, and risk category thresholds."""
    metrics = MLService.get_metrics()
    return jsonify({
        "success": True,
        "data": {
            "model_type": metrics.get("model_type", "RandomForestClassifier"),
            "n_estimators": metrics.get("n_estimators", 100),
            "class_weight": metrics.get("class_weight", "balanced"),
            "risk_categories": {
                "NORMAL": "Fraud Probability < 0.25",
                "SUSPICIOUS": "0.25 <= Fraud Probability < 0.70",
                "HIGH_RISK": "Fraud Probability >= 0.70"
            },
            "features_required": [
                "amount_inr", "hour_of_day", "day_of_week", "is_weekend",
                "tx_frequency_last_24h", "balance_before_inr", "balance_ratio",
                "customer_hist_avg_inr", "amount_to_avg_ratio", "time_since_last_tx_min",
                "is_rapid_succession", "tx_type"
            ],
            "evaluation_summary": {
                "accuracy": metrics.get("random_forest_metrics", {}).get("accuracy"),
                "precision": metrics.get("random_forest_metrics", {}).get("precision"),
                "recall": metrics.get("random_forest_metrics", {}).get("recall"),
                "f1_score": metrics.get("random_forest_metrics", {}).get("f1_score"),
                "roc_auc": metrics.get("random_forest_metrics", {}).get("roc_auc")
            }
        }
    }), 200


@ml_bp.route("/metrics", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_detailed_metrics():
    """Admin-only endpoint returning full evaluation metrics and baseline comparison."""
    metrics = MLService.get_metrics()
    return jsonify({
        "success": True,
        "data": metrics
    }), 200


@ml_bp.route("/transactions/flagged", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_flagged_transactions():
    """Admin-only endpoint to retrieve all suspicious and high-risk transactions."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 20))))
    except ValueError:
        raise ValidationError("Query parameters 'page' and 'limit' must be positive integers")

    db = mongo_manager.get_db()
    query = {"risk_level": {"$in": ["SUSPICIOUS", "HIGH_RISK"]}}

    skip = (page - 1) * limit
    total = db.transactions.count_documents(query)
    cursor = db.transactions.find(query).sort("timestamp", -1).skip(skip).limit(limit)

    return jsonify({
        "success": True,
        "data": {
            "flagged_transactions": [Transaction.serialize(doc) for doc in cursor],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 1
            }
        }
    }), 200
