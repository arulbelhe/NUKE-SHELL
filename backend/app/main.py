from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from .config import settings
from .db import get_db, init_db
from .rate_limit import login_rate_limiter
from .security import (
    build_expiry,
    from_iso,
    generate_token,
    hash_password,
    token_hash,
    to_iso,
    utc_now,
    verify_password,
)

app = FastAPI(title="RTS Auth Service", version="0.1.0")


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: Optional[str] = Field(default=None, max_length=128)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_at: str
    refresh_expires_at: str


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/client/version")
def client_version(version: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT version, is_minimum, is_allowed, message FROM client_versions WHERE version = ?",
            (version,),
        ).fetchone()
        min_row = conn.execute(
            "SELECT version, message FROM client_versions WHERE is_minimum = 1 LIMIT 1"
        ).fetchone()

    minimum_version = min_row["version"] if min_row else "0.1.0"
    minimum_message = min_row["message"] if min_row else ""

    if row:
        allowed = bool(row["is_allowed"])
        return {
            "version": row["version"],
            "is_allowed": allowed,
            "minimum_version": minimum_version,
            "message": row["message"] if not allowed else "",
        }

    return {
        "version": version,
        "is_allowed": False,
        "minimum_version": minimum_version,
        "message": minimum_message or "Client version is not supported.",
    }


def issue_session(user_id: int, ip: str | None, user_agent: str | None) -> AuthResponse:
    access_token = generate_token()
    refresh_token = generate_token()
    created_at = to_iso(utc_now())
    access_expires_at = build_expiry(settings.access_token_ttl_seconds)
    refresh_expires_at = build_expiry(settings.refresh_token_ttl_seconds)

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO sessions(
                user_id, access_token_hash, refresh_token_hash, created_at, access_expires_at,
                expires_at, ip_created, user_agent
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                token_hash(access_token),
                token_hash(refresh_token),
                created_at,
                access_expires_at,
                refresh_expires_at,
                ip,
                user_agent,
            ),
        )

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (payload.username, payload.email),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="username_or_email_taken")

        created_at = to_iso(utc_now())
        conn.execute(
            """
            INSERT INTO users(username, email, password_hash, is_active, is_banned, created_at)
            VALUES(?, ?, ?, 1, 0, ?)
            """,
            (payload.username, payload.email, hash_password(payload.password), created_at),
        )

    return {"status": "registered"}


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not login_rate_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="too_many_login_attempts")

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, password_hash, is_active, is_banned FROM users WHERE username = ?",
            (payload.username,),
        ).fetchone()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not bool(user["is_active"]):
        raise HTTPException(status_code=403, detail="account_inactive")
    if bool(user["is_banned"]):
        raise HTTPException(status_code=403, detail="account_banned")

    return issue_session(
        user_id=user["id"],
        ip=client_ip,
        user_agent=request.headers.get("user-agent"),
    )


def get_current_session(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer_token")
    access_token = authorization.removeprefix("Bearer ").strip()
    access_hash = token_hash(access_token)

    with get_db() as conn:
        session = conn.execute(
            """
            SELECT s.id, s.user_id, s.access_expires_at, s.expires_at, s.revoked_at,
                   u.username, u.is_active, u.is_banned
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.access_token_hash = ?
            """,
            (access_hash,),
        ).fetchone()

    if not session:
        raise HTTPException(status_code=401, detail="invalid_session")
    if session["revoked_at"] is not None:
        raise HTTPException(status_code=401, detail="session_revoked")
    if from_iso(session["access_expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="access_token_expired")
    if from_iso(session["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="session_expired")
    if not bool(session["is_active"]):
        raise HTTPException(status_code=403, detail="account_inactive")
    if bool(session["is_banned"]):
        raise HTTPException(status_code=403, detail="account_banned")

    return session


@app.get("/me")
def me(session=Depends(get_current_session)):
    return {"id": session["user_id"], "username": session["username"]}


@app.post("/auth/logout")
def logout(payload: LogoutRequest, authorization: str = Header(default="")):
    token_candidate = None
    token_field = None
    if authorization.startswith("Bearer "):
        token_candidate = authorization.removeprefix("Bearer ").strip()
        token_field = "access_token_hash"
    elif payload.refresh_token:
        token_candidate = payload.refresh_token
        token_field = "refresh_token_hash"

    if not token_candidate or not token_field:
        raise HTTPException(status_code=400, detail="missing_token")

    token_h = token_hash(token_candidate)
    with get_db() as conn:
        result = conn.execute(
            f"UPDATE sessions SET revoked_at = ? WHERE {token_field} = ? AND revoked_at IS NULL",
            (to_iso(utc_now()), token_h),
        )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="session_not_found")

    return {"status": "logged_out"}


@app.post("/auth/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, request: Request):
    refresh_hash = token_hash(payload.refresh_token)

    with get_db() as conn:
        session = conn.execute(
            """
            SELECT id, user_id, expires_at, revoked_at
            FROM sessions WHERE refresh_token_hash = ?
            """,
            (refresh_hash,),
        ).fetchone()

    if not session:
        raise HTTPException(status_code=401, detail="invalid_refresh_token")
    if session["revoked_at"] is not None:
        raise HTTPException(status_code=401, detail="session_revoked")
    if from_iso(session["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="refresh_token_expired")

    new_access = generate_token()
    new_refresh = generate_token()
    access_expires_at = build_expiry(settings.access_token_ttl_seconds)
    refresh_expires_at = build_expiry(settings.refresh_token_ttl_seconds)

    with get_db() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET access_token_hash = ?, refresh_token_hash = ?, access_expires_at = ?, expires_at = ?
            WHERE id = ?
            """,
            (
                token_hash(new_access),
                token_hash(new_refresh),
                access_expires_at,
                refresh_expires_at,
                session["id"],
            ),
        )

    return AuthResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )
