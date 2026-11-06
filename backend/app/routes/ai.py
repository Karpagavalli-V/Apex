from flask import Blueprint, request, jsonify, g, current_app
from app.utils.auth_guards import jwt_required
from app.utils.errors import ValidationError
from app.services.ai_service import AIService

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

@ai_bp.route("/financial-summary", methods=["GET"])
@jwt_required
def get_financial_summary():
    """
    Returns AI Monthly Financial Summary, category-free arithmetic metrics,
    and Month-over-Month comparison for the authenticated user.
    Query param: ?month=YYYY-MM (optional)
    """
    current_user = g.current_user
    month_arg = request.args.get("month")
    
    summary_data = AIService.generate_financial_summary(
        user_id=current_user["user_id"],
        month=month_arg
    )

    return jsonify({
        "success": True,
        "message": "Monthly financial summary generated successfully",
        "data": summary_data
    }), 200


@ai_bp.route("/spending-analysis", methods=["GET"])
@jwt_required
def get_spending_analysis():
    """
    Analyzes user outflow velocity, patterns, and high-value spending outliers
    over a specified historical window without assuming missing expense categories.
    Query param: ?days=30 (optional, 7-365)
    """
    current_user = g.current_user
    days_arg = request.args.get("days", "30")
    
    try:
        days = int(days_arg)
    except ValueError:
        raise ValidationError("Query parameter 'days' must be a valid integer.")

    analysis_data = AIService.generate_spending_analysis(
        user_id=current_user["user_id"],
        days=days
    )

    return jsonify({
        "success": True,
        "message": "Spending analysis generated successfully",
        "data": analysis_data
    }), 200


@ai_bp.route("/savings-suggestions", methods=["GET"])
@jwt_required
def get_savings_suggestions():
    """
    Generates conservative, practical savings targets and budgeting recommendations
    grounded strictly in actual cash flow and account balance runway.
    """
    current_user = g.current_user
    savings_data = AIService.generate_savings_suggestions(
        user_id=current_user["user_id"]
    )

    return jsonify({
        "success": True,
        "message": "Savings suggestions generated successfully",
        "data": savings_data
    }), 200


@ai_bp.route("/chat", methods=["POST"])
@jwt_required
def chat_financial_assistant():
    """
    Conversational AI Financial Assistant answering user questions about spending,
    largest transactions, savings tips, financial summary, and fraud risk levels.
    Enforces security guardrail: strictly blocks transaction execution attempts.
    """
    current_user = g.current_user
    body = request.get_json(silent=True) or {}
    
    message = body.get("message")
    if not message or not isinstance(message, str) or not message.strip():
        raise ValidationError("Request body must include a non-empty string in 'message'.")

    transaction_id = body.get("transaction_id")
    if transaction_id and not isinstance(transaction_id, str):
        raise ValidationError("'transaction_id' must be a string if provided.")

    chat_response = AIService.process_chat(
        user_id=current_user["user_id"],
        message=message.strip(),
        transaction_id=transaction_id.strip() if transaction_id else None
    )

    return jsonify({
        "success": True,
        "message": "AI assistant response generated",
        "data": chat_response
    }), 200


@ai_bp.route("/provider-info", methods=["GET"])
@jwt_required
def get_provider_info():
    """Returns metadata regarding active LLM provider configuration and capabilities."""
    provider = current_app.config.get("LLM_PROVIDER", "gemini")
    model = (
        current_app.config.get("GEMINI_MODEL") 
        if provider == "gemini" 
        else current_app.config.get("OPENAI_MODEL")
    )
    
    return jsonify({
        "success": True,
        "data": {
            "provider": provider,
            "model": model,
            "rate_limit_per_minute": current_app.config.get("AI_RATE_LIMIT_PER_MINUTE", 30),
            "fallback_on_error": current_app.config.get("AI_FALLBACK_ON_ERROR", True)
        }
    }), 200
