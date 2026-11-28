from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Adaptive UI Service"
    app_version: str = "0.1.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    openproject_url: str = "http://localhost:3000"
    openproject_api_token: str = ""
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    index_dir: Path = Path(__file__).resolve().parents[2] / "data" / "index"

    model_config = SettingsConfigDict(
        env_file="adaptive_ui_service/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
