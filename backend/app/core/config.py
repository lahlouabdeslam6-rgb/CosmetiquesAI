from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cosmetiques API"
    app_version: str = "0.1.0"
    environment: str = "development"

    mongodb_url: str
    mongodb_database: str = "cosmetiques"
    sqlite_url: str = "sqlite+aiosqlite:///./data/cosmetiques.db"
    redis_url: str = "redis://redis:6379/0"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "cosmetiques_products"
    ollama_url: str = "http://ollama:11434"
    ollama_chat_model: str = "qwen2.5:3b"
    ollama_laboratory_model: str = ""
    ollama_embedding_model: str = "nomic-embed-text"
    automation_api_key: str = "local-automation-key-change-me"
    local_media_enabled: bool = True
    local_media_model_id: str = "OpenVINO/stable-diffusion-v1-5-fp16-ov"
    local_media_model_dir: str = "/app/data/media-models/stable-diffusion-v1-5-fp16-ov"
    local_media_device: str = "CPU"
    local_media_steps: int = 12

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
