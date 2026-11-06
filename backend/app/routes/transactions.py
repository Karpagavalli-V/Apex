from flask import Blueprint, request, jsonify
from app.utils.auth_guards import jwt_required, get_current_user
from app.services.banking_service import BankingService
from app.extensions import mongo_manager
from app.models.transaction import Transaction
from app.utils.errors import NotFoundError, AuthorizationError, ValidationError

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")

@transactions_bp.route("/my-history", methods=["GET"])
@jwt_required
def get_user_transaction_history():
    """
    Retrieves aggregated, paginated transaction history across all accounts
    belonging to the authenticated customer.
    """
    user = get_current_user()
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        raise ValidationError("Query parameters 'page' and 'limit' must be positive integers")

    tx_type = request.args.get("type", "").strip() or None

    result = BankingService.get_user_transactions(
        user_id=user["user_id"],
        page=page,
        limit=limit,
        tx_type=tx_type
    )

    return jsonify({
        "success": True,
        "data": result
    }), 200


@transactions_bp.route("/<transaction_id>", methods=["GET"])
@jwt_required
def get_transaction_detail(transaction_id: str):
    """Retrieves single transaction details (owner or admin only)."""
    user = get_current_user()
    db = mongo_manager.get_db()
    tx = db.transactions.find_one({"transaction_id": transaction_id})
    if not tx:
        raise NotFoundError("Transaction not found")

    is_admin = user.get("role") == "admin"
    is_owner = tx.get("user_id") == user.get("user_id")

    if not (is_admin or is_owner):
        raise AuthorizationError("You do not have permission to view this transaction")

    return jsonify({
        "success": True,
        "data": {
            "transaction": Transaction.serialize(tx)
        }
    }), 200
