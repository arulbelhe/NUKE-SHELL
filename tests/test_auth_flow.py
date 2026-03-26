from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["AUTH_DB_PATH"] = "./tests/test_auth.db"
os.environ["AUTH_TOKEN_PEPPER"] = "test-pepper"

from backend.app.main import app  # noqa: E402


client = TestClient(app)


def setup_module():
    db = Path("./tests/test_auth.db")
    if db.exists():
        db.unlink()


def test_register_login_me_logout():
    r = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "password123"},
    )
    assert r.status_code == 201

    bad = client.post("/auth/login", json={"username": "alice", "password": "wrongpass"})
    assert bad.status_code == 401

    login = client.post("/auth/login", json={"username": "alice", "password": "password123"})
    assert login.status_code == 200
    tokens = login.json()

    me = client.get("/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"}, json={})
    assert logout.status_code == 200


def test_version_endpoint():
    ok = client.get("/client/version", params={"version": "0.1.0"})
    assert ok.status_code == 200
    assert ok.json()["is_allowed"] is True

    blocked = client.get("/client/version", params={"version": "0.0.1"})
    assert blocked.status_code == 200
    assert blocked.json()["is_allowed"] is False
