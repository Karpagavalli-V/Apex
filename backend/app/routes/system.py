from flask import Blueprint, jsonify
from app.extensions import mongo_manager

system_bp = Blueprint("system", __name__, url_prefix="/api/system")

@system_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint reporting API and database status."""
    is_db_healthy = mongo_manager.is_healthy()
    status_str = "healthy" if is_db_healthy else "degraded"
    
    return jsonify({
        "status": status_str,
        "database": {
            "connected": is_db_healthy,
            "supports_transactions": mongo_manager.supports_transactions,
            "transaction_mode": "replica_set" if mongo_manager.supports_transactions else "standalone_atomic"
        },
        "version": "1.0.0"
    }), 200 if is_db_healthy else 503
