"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All settings loaded from environment variables or .env file."""

    # Core (no defaults — must be set via env or .env)
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str = ""
    apollo_api_key: str
    openai_api_key: str

    # Redis (Celery + SSE pub/sub)
    redis_url: str = "redis://localhost:6379/0"

    # Agent system
    agent_internal_secret: str = ""

    # Feature flags
    icp_builder_enabled: bool = True
    log_level: str = "info"

    # CORS
    cors_origins: str = "http://localhost:3001"

    # Directories
    context_dir: str = "context"
    offers_dir: str = "offers"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()
