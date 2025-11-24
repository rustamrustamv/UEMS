from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "University Education Management System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/uems"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Stripe
    STRIPE_API_KEY: str = "sk_test_your_stripe_key"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_webhook_secret"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_your_publishable_key"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Metrics
    ENABLE_METRICS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
