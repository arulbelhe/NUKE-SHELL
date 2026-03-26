from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("AUTH_DB_PATH", "./backend/auth.db")
    token_pepper: str = os.getenv("AUTH_TOKEN_PEPPER", "dev-token-pepper-change-me")
    access_token_ttl_seconds: int = int(os.getenv("AUTH_ACCESS_TOKEN_TTL_SECONDS", "900"))
    refresh_token_ttl_seconds: int = int(os.getenv("AUTH_REFRESH_TOKEN_TTL_SECONDS", "2592000"))
    login_attempt_window_seconds: int = int(os.getenv("AUTH_LOGIN_WINDOW_SECONDS", "300"))
    login_attempt_limit: int = int(os.getenv("AUTH_LOGIN_ATTEMPT_LIMIT", "5"))


settings = Settings()
