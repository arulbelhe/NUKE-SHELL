from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .config import settings

password_hasher = PasswordHasher()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime) -> str:
    return value.isoformat()


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def hash_password(raw_password: str) -> str:
    return password_hasher.hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, raw_password)
    except VerifyMismatchError:
        return False


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def token_hash(token: str) -> str:
    return hmac.new(settings.token_pepper.encode(), token.encode(), hashlib.sha256).hexdigest()


def build_expiry(seconds: int) -> str:
    return to_iso(utc_now() + timedelta(seconds=seconds))
