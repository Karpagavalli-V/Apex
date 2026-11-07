import re
from flask import Blueprint, request, jsonify
from app.extensions import mongo_manager
from app.utils.auth_guards import jwt_required, roles_required, get_current_user
from app.utils.validators import (
    validate_account_creation_payload,
    validate_transaction_payload,
    validate_transfer_payload
)
from app.services.banking_service import BankingService
from app.utils.errors import ValidationError

accounts_bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")

def _get_idempotency_key() -> str:
    """Extracts Idempotency-Key from headers if present."""
    return request.headers.get("Idempotency-Key", "").strip() or None


@accounts_bp.route("", methods=["POST"])
@jwt_required
def create_account():
    """
    Creates a new bank account for the authenticated customer.
    Supports optional initial deposit and idempotency key.
    """
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    validated = validate_account_creation_payload(data)
    idempotency_key = _get_idempotency_key()

    result = BankingService.create_account(
        user_id=user["user_id"],
        account_type=validated["account_type"],
        initial_deposit_paise=validated["initial_deposit_paise"],
        idempotency_key=idempotency_key
    )

    return jsonify({
        "success": True,
        "message": "Account created successfully",
        "data": result
    }), 201


@accounts_bp.route("", methods=["GET"])
@jwt_required
def list_my_accounts():
    """Returns all bank accounts belonging to the authenticated customer."""
    user = get_current_user()
    accounts = BankingService.get_user_accounts(user["user_id"])

    return jsonify({
        "success": True,
        "data": {
            "accounts": accounts,
            "count": len(accounts)
        }
    }), 200


@accounts_bp.route("/all", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_all_accounts_admin():
    """Admin-only endpoint to list all accounts across all customers with pagination."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 20))))
    except ValueError:
        raise ValidationError("Query parameters 'page' and 'limit' must be positive integers")

    result = BankingService.get_all_accounts(page=page, limit=limit)
    return jsonify({
        "success": True,
        "data": result
    }), 200


@accounts_bp.route("/lookup-beneficiary", methods=["GET"])
@jwt_required
def lookup_beneficiary():
    """
    GPay-style dynamic search for registered beneficiaries by:
    - Name (e.g. 'Charu')
    - Username (e.g. 'charu_01')
    - Apex Pay ID (e.g. 'charu_01@apex')
    - Phone number (e.g. '98765' or '+91 98765 01001')
    - Account number (e.g. '100466777930')
    Returns list of verified recipient cards with their active account details.
    """
    current_user = get_current_user()
    db = mongo_manager.get_db()
    q = request.args.get("q", "").strip()

    beneficiaries = []

    if q:
        clean_q = re.escape(q)
        digits_only = "".join(filter(str.isdigit, q))

        user_criteria = [
            {"full_name": {"$regex": clean_q, "$options": "i"}},
            {"username": {"$regex": clean_q, "$options": "i"}},
            {"apex_pay_id": {"$regex": clean_q, "$options": "i"}},
            {"email": {"$regex": clean_q, "$options": "i"}},
        ]
        if len(digits_only) >= 3:
            user_criteria.append({"phone_number": {"$regex": re.escape(digits_only)}})

        matched_users = list(db.users.find({"$or": user_criteria, "is_active": True}).limit(10))
        user_ids = [u["user_id"] for u in matched_users]

        # Also match direct account number
        if len(digits_only) >= 3:
            acc_matches = list(db.accounts.find({"account_number": {"$regex": re.escape(digits_only)}, "status": "ACTIVE"}).limit(5))
            for acc in acc_matches:
                if acc["user_id"] not in user_ids:
                    u = db.users.find_one({"user_id": acc["user_id"]})
                    if u and u.get("is_active", True):
                        matched_users.append(u)
                        user_ids.append(u["user_id"])
    else:
        # Default: return other registered active customers as suggestions
        matched_users = list(db.users.find({
            "user_id": {"$ne": current_user["user_id"]},
            "role": "customer",
            "is_active": True
        }).limit(8))

    seen_accounts = set()
    for u in matched_users:
        u_accs = list(db.accounts.find({"user_id": u["user_id"], "status": "ACTIVE"}))
        for acc in u_accs:
            if acc["account_id"] in seen_accounts:
                continue
            seen_accounts.add(acc["account_id"])
            is_self = (u["user_id"] == current_user["user_id"])
            username = u.get("username", "")
            pay_id = u.get("apex_pay_id") or (f"{username.lower()}@apex" if username else "")
            beneficiaries.append({
                "user_id": u["user_id"],
                "full_name": u.get("full_name") or username,
                "username": username,
                "apex_pay_id": pay_id,
                "phone_number": u.get("phone_number", ""),
                "account_id": acc["account_id"],
                "account_number": acc["account_number"],
                "account_type": acc.get("account_type", "SAVINGS"),
                "is_self": is_self
            })

    return jsonify({
        "success": True,
        "data": beneficiaries
    }), 200


@accounts_bp.route("/<account_id>", methods=["GET"])
@jwt_required
def get_account_details(account_id: str):
    """Retrieves full details for a single account (owner or admin only)."""
    user = get_current_user()
    account = BankingService.get_account_by_id(account_id, requesting_user=user)

    return jsonify({
        "success": True,
        "data": {
            "account": account
        }
    }), 200


@accounts_bp.route("/<account_id>/balance", methods=["GET"])
@jwt_required
def get_account_balance(account_id: str):
    """
    Dedicated balance inquiry endpoint for an account.
    Returns both integer paise and formatted INR figures.
    """
    user = get_current_user()
    account = BankingService.get_account_by_id(account_id, requesting_user=user)

    return jsonify({
        "success": True,
        "data": {
            "account_id": account["account_id"],
            "account_number": account["account_number"],
            "account_type": account["account_type"],
            "balance_paise": account["balance_paise"],
            "balance_inr": account["balance_inr"],
            "currency": account["currency"],
            "status": account["status"],
            "updated_at": account.get("updated_at")
        }
    }), 200


@accounts_bp.route("/<account_id>/deposit", methods=["POST"])
@jwt_required
def deposit_funds(account_id: str):
    """
    Deposits funds into an account atomically.
    Validates amount in paise, checks idempotency, and records ledger entry.
    """
    user = get_current_user()
    data = request.get_json(silent=True)
    validated = validate_transaction_payload(data)
    idempotency_key = _get_idempotency_key()

    result = BankingService.deposit(
        account_id=account_id,
        amount_paise=validated["amount_paise"],
        requesting_user=user,
        description=validated["description"],
        idempotency_key=idempotency_key
    )

    return jsonify({
        "success": True,
        "message": "Deposit processed successfully",
        "data": result
    }), 200


@accounts_bp.route("/<account_id>/withdraw", methods=["POST"])
@jwt_required
def withdraw_funds(account_id: str):
    """
    Withdraws funds from an account atomically.
    Strictly prevents overdrafts via conditional atomic database updates.
    """
    user = get_current_user()
    data = request.get_json(silent=True)
    validated = validate_transaction_payload(data)
    idempotency_key = _get_idempotency_key()

    result = BankingService.withdraw(
        account_id=account_id,
        amount_paise=validated["amount_paise"],
        requesting_user=user,
        description=validated["description"],
        idempotency_key=idempotency_key
    )

    return jsonify({
        "success": True,
        "message": "Withdrawal processed successfully",
        "data": result
    }), 200


@accounts_bp.route("/<account_id>/transfer", methods=["POST"])
@jwt_required
def transfer_funds(account_id: str):
    """Transfers funds between accounts atomically."""
    user = get_current_user()
    data = request.get_json(silent=True)
    validated = validate_transfer_payload(data)
    idempotency_key = _get_idempotency_key()

    result = BankingService.transfer(
        source_account_id=account_id,
        target_account_identifier=validated["target_account"],
        amount_paise=validated["amount_paise"],
        requesting_user=user,
        description=validated["description"],
        idempotency_key=idempotency_key
    )

    return jsonify({
        "success": True,
        "message": "Transfer processed successfully",
        "data": result
    }), 200


@accounts_bp.route("/<account_id>/transactions", methods=["GET"])
@jwt_required
def get_account_transactions(account_id: str):
    """Returns paginated transaction history for a specific account."""
    user = get_current_user()
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        raise ValidationError("Query parameters 'page' and 'limit' must be positive integers")

    tx_type = request.args.get("type", "").strip() or None
    sort_dir = request.args.get("sort", "desc").strip()

    result = BankingService.get_account_transactions(
        account_id=account_id,
        requesting_user=user,
        page=page,
        limit=limit,
        tx_type=tx_type,
        sort_dir=sort_dir
    )

    return jsonify({
        "success": True,
        "data": result
    }), 200
