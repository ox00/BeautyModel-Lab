from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # Project paths (settings.py is at backend/app/config/settings.py)
    PROJECT_ROOT: str = str(Path(__file__).resolve().parents[2])  # -> backend/
    CONFIG_DIR: str = str(Path(__file__).resolve().parents[2] / "config")  # -> backend/config/
    DATA_DIR: str = str(Path(__file__).resolve().parents[2] / "data")  # -> backend/data/

    # Keyword CSV path
    TREND_KEYWORD_CSV: str = str(Path(__file__).resolve().parents[2] / "config" / "trend-keyword.csv")
    KEYWORD_SKILL_PATH: str = str(Path(__file__).resolve().parents[2] / "config" / "enhance_trend_keyword.md")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:123456@localhost:5433/media_crawler"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:123456@localhost:5433/media_crawler"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MediaCrawler
    MEDIACRAWLER_DIR: str = str(
        (Path(__file__).resolve().parents[2] / ".." / "MediaCrawler-main" / "MediaCrawler-main").resolve()
    )

    # LLM Configuration (for Cleaning Agent)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    # Security
    ACCOUNT_ENCRYPTION_KEY: str = "change-me-in-production-32bytes!!"

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    model_config = {"env_file": str(Path(__file__).resolve().parents[2] / ".env"), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
