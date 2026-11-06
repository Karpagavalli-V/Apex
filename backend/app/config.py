import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-jwt-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24")))
    
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?replicaSet=rs0&directConnection=true")
    DB_NAME = os.getenv("DB_NAME", "banking_dev")
    
    CORS_ORIGINS = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = False
    TESTING = False

    # Generative AI & LLM Provider Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AI_RATE_LIMIT_PER_MINUTE = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "30"))
    AI_FALLBACK_ON_ERROR = os.getenv("AI_FALLBACK_ON_ERROR", "true").lower() in ("true", "1", "yes")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Test environment configuration: strictly isolated database."""
    TESTING = True
    DEBUG = False
    DB_NAME = os.getenv("TEST_DB_NAME", "banking_test")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class ProductionConfig(Config):
    """Production environment configuration with strict validation."""
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
