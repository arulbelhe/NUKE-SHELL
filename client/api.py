from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class APIClient:
    base_url: str
    verify_tls: bool = True

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=10.0, verify=self.verify_tls)

    def check_version(self, version: str) -> dict:
        with self._client() as client:
            resp = client.get("/client/version", params={"version": version})
            resp.raise_for_status()
            return resp.json()

    def login(self, username: str, password: str) -> dict:
        with self._client() as client:
            resp = client.post("/auth/login", json={"username": username, "password": password})
            if resp.status_code >= 400:
                return {"error": resp.json().get("detail", "login_failed")}
            return resp.json()

    def register(self, username: str, password: str, email: Optional[str] = None) -> dict:
        with self._client() as client:
            resp = client.post(
                "/auth/register",
                json={"username": username, "password": password, "email": email},
            )
            if resp.status_code >= 400:
                return {"error": resp.json().get("detail", "register_failed")}
            return resp.json()

    def me(self, access_token: str) -> dict:
        with self._client() as client:
            resp = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
            if resp.status_code >= 400:
                return {"error": resp.json().get("detail", "me_failed")}
            return resp.json()

    def logout(self, access_token: str) -> dict:
        with self._client() as client:
            resp = client.post(
                "/auth/logout",
                json={},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code >= 400:
                return {"error": resp.json().get("detail", "logout_failed")}
            return resp.json()
