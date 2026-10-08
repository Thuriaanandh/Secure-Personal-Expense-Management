from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure Personal Expense Management Application"
    PROJECT_VERSION: str = "1.1.0"
    APP_NAME: str = "Secure Personal Expense Management Application"
    APP_VERSION: str = "1.1.0"
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Cryptographic secret key: must be at least 32 characters in production
    SECRET_KEY: str = Field(
        default="development-insecure-secret-key-replace-in-production-min-32-chars",
        alias="SECRET_KEY",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./spema_ledger.db", alias="DATABASE_URL")

    # Rate Limiting
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 900  # 15 minutes

    model_config = {"env_file": ".env", "extra": "ignore"}


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        if _settings.APP_ENV == "production" and len(_settings.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long in production.")
    return _settings
