from app.routes.auth import auth_bp
from app.routes.system import system_bp
from app.routes.accounts import accounts_bp
from app.routes.transactions import transactions_bp
from app.routes.ml import ml_bp
from app.routes.ai import ai_bp

__all__ = ["auth_bp", "system_bp", "accounts_bp", "transactions_bp", "ml_bp", "ai_bp"]

