from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SessionCredentials:
    access_token: str
    refresh_token: str
    access_expires_at: str
    refresh_expires_at: str


class SessionStore:
    def __init__(self, filepath: str) -> None:
        self.path = Path(filepath)

    def load(self) -> Optional[SessionCredentials]:
        if not self.path.exists():
            return None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return SessionCredentials(**raw)

    def save(self, creds: SessionCredentials) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(creds), indent=2), encoding="utf-8")
        os.chmod(self.path, 0o600)

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
