from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClientConfig:
    api_base_url: str
    client_version: str
    verify_tls: bool
    session_file: str



def load_config(path: str) -> ClientConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return ClientConfig(
        api_base_url=raw["api_base_url"],
        client_version=raw["client_version"],
        verify_tls=bool(raw.get("verify_tls", True)),
        session_file=raw.get("session_file", ".session.json"),
    )
