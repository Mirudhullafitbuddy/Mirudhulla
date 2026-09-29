from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "FitBuddy"
    database_url: str = f"sqlite:///{BASE_DIR / 'fitbuddy.db'}"
    gemini_api_key: str = ""
    gemini_workout_model: str = "gemini-2.5-flash"
    gemini_tip_model: str = "gemini-2.5-flash"
    admin_key: str = "change-this-for-local-admin"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
