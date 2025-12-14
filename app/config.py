from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://pythia_user:pythia_pass@localhost:5432/pythia_db"

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration
    llm_provider: str = "gemini"
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 30

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 3600

    # Feature Extraction
    severity_threshold_critical: float = 50.0
    severity_threshold_high: float = 25.0
    severity_threshold_medium: float = 10.0

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Server
    port: int = 8000
    workers: int = 4
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
