"""Centralized application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/startuptracker"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # OpenAI / LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: int = 30

    # LLM extraction cache
    llm_cache_max_size: int = 1024

    # RSS fallback
    feed_urls: str = ""


settings = Settings()
