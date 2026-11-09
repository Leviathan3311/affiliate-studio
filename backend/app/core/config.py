import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # GP_ENV_FILE="" disables .env (tests must never pick up real keys)
    model_config = SettingsConfigDict(
        env_file=os.environ.get("GP_ENV_FILE", ".env") or None, extra="ignore"
    )

    env: str = "dev"
    database_url: str = "sqlite:///./growthpilot.db"
    secret_key: str = "dev-only-secret-change-me-in-production-0000"
    # Fernet key for page tokens; derived from secret_key when empty (dev only).
    token_encryption_key: str = ""
    access_token_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"

    # Billing (manual bank transfer, confirmed by a platform admin)
    trial_days: int = 14
    plan_price_vnd: int = 499000
    bank_bin: str = ""  # NAPAS BIN, e.g. 970436 = Vietcombank
    bank_account: str = ""
    bank_account_name: str = ""
    platform_admin_emails: list[str] = []

    # Outgoing email (password reset). Gmail: smtp.gmail.com + an App Password.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

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
    # Stream 2 (research, scripts, viral cut): Gemini 3.8 Flash; deep research on 2.5 Pro
    # 2.5 Pro is closed to new keys; 3.1 Pro needs billing and falls back to the chain below.
    gemini_deep_model: str = "gemini-3.1-pro-preview"
    # Tried in order when the primary is overloaded (503) or out of quota (429)
    gemini_fallback_models: list[str] = ["gemini-3-flash-preview", "gemini-3.1-flash-lite"]
    research_timeout_seconds: float = 180.0
    # Google Search grounding needs a billed Gemini key; without it research cites only
    # the public URLs the user attached to the project (BRD MOD-03A MVP scope).
    gemini_search: bool = False
    gemini_embedding_model: str = "gemini-embedding-2"
    # Vietnamese voiceover per shot (app/ai/speech.py); the first model that answers is used
    gemini_tts_models: list[str] = ["gemini-3.8-flash-lite-tts", "gemini-3.8-flash-tts"]
    gemini_tts_voice: str = "Sulafat"  # "warm"
    gemini_tts_style: str = "warm, calm and gentle, like a friendly shop consultant"

    # LightRAG knowledge layer (system design §3.2); needs Postgres + Gemini, else keyword fallback
    lightrag_enabled: bool = True
    lightrag_llm_model: str = "gemini-3.1-flash-lite"
    # Supabase CA file (Project Settings -> Database -> SSL) for verify-full TLS from LightRAG
    postgres_ssl_root_cert: str = ""
    knowledge_sync_seconds: int = 120

    # Langfuse Cloud (system design §3.3); empty keys = tracing off
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"

    # Object storage (system design §1 rule 2: media never in the DB). Empty r2_* = local disk.
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "growthpilot-media"
    local_media_dir: str = "./media"
    presign_seconds: int = 6 * 3600
    max_upload_mb: int = 500
    storage_quota_mb: int = 10 * 1024  # R2 free tier

    # Kaggle media workers authenticate with this token (Kaggle Secret MEDIA_WORKER_TOKEN)
    media_worker_token: str = ""
    media_job_stale_minutes: int = 20
    # Modal app with the GPU workers (notebooks/modal/growthpilot.py); empty = start Kaggle by hand.
    # Auth: ~/.modal.toml locally, MODAL_TOKEN_ID / MODAL_TOKEN_SECRET on a server.
    modal_app: str = ""

    # Optional Upstash Redis REST queue filled by the Cloudflare webhook edge gateway at night
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    worker_poll_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    weak_key = s.secret_key.startswith("dev-only") or len(s.secret_key) < 32
    if s.env != "dev" and (weak_key or not s.meta_app_secret):
        raise RuntimeError(
            "SECRET_KEY (32+ characters) and META_APP_SECRET must be set outside dev"
        )
    return s
