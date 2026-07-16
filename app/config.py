"""
Central application configuration, loaded from environment variables / .env
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Personal Finance & Expense Tracker"
    env: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./finance_tracker.db"

    secret_key: str = "insecure-dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    openai_api_key: str = ""
    gemini_api_key: str = ""
    ai_provider: str = "none"  # openai | gemini | none

    default_currency: str = "INR"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
