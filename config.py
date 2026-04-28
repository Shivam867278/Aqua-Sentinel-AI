from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("AQUA_APP_NAME", "Aqua Sentinel AI")
    api_host: str = os.getenv("AQUA_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("AQUA_API_PORT", "5000"))
    api_base_url: str = os.getenv("AQUA_API_BASE_URL", "http://127.0.0.1:5000")
    environment: str = os.getenv("AQUA_ENV", "development")
    cors_origins: str = os.getenv("AQUA_CORS_ORIGINS", "*")
    request_timeout_seconds: int = int(os.getenv("AQUA_REQUEST_TIMEOUT_SECONDS", "8"))
    enable_local_fallback: bool = os.getenv("AQUA_ENABLE_LOCAL_FALLBACK", "true").lower() == "true"
    developer_name: str = os.getenv("AQUA_DEVELOPER_NAME", "Shivam")
    database_url: str = os.getenv("AQUA_DATABASE_URL", "sqlite:///data/aqua_sentinel.db")
    auth_token_hours: int = int(os.getenv("AQUA_AUTH_TOKEN_HOURS", "12"))


settings = Settings()
