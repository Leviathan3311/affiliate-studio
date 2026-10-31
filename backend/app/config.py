from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    database_url: str = "sqlite:///./growthpilot.db"
    secret_key: str = "dev-only-secret-change-me-in-production-0000"
    # Fernet key for page tokens; derived from secret_key when empty (dev only).
    token_encryption_key: str = ""
    access_token_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"

    # Meta Graph API (MOD-06)
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = "growthpilot-verify"
    meta_graph_version: str = "v24.0"
    # True = never call the Send API; outbound messages are recorded as dry_run.
    meta_dry_run: bool = True

    # LLM Router (system design §3): stream 1 = Groq Qwen primary, Gemini fallback
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    llm_timeout_seconds: float = 20.0

    worker_poll_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.env != "dev" and (s.secret_key.startswith("dev-only") or not s.meta_app_secret):
        raise RuntimeError("SECRET_KEY and META_APP_SECRET must be set outside dev")
    return s
