from __future__ import annotations

import argparse
import socket

from client.api import APIClient
from client.config import load_config
from client.logger import build_logger
from client.session_store import SessionCredentials, SessionStore
from client.state_machine import AuthState


def has_network() -> bool:
    try:
        socket.gethostbyname("localhost")
        return True
    except socket.gaierror:
        return False


def run(config_path: str) -> int:
    state = AuthState.BOOT
    logger = build_logger("client-auth")

    logger.info("boot", extra={"event": state.value})
    state = AuthState.LOAD_CONFIG
    config = load_config(config_path)
    api = APIClient(base_url=config.api_base_url, verify_tls=config.verify_tls)
    sessions = SessionStore(config.session_file)

    state = AuthState.CHECK_NETWORK
    if not has_network():
        logger.error("network_unavailable", extra={"event": state.value})
        return 1

    state = AuthState.VERSION_CHECK
    try:
        version_resp = api.check_version(config.client_version)
    except Exception as exc:
        logger.error(f"version_check_failed:{exc}", extra={"event": state.value})
        return 1

    if not version_resp.get("is_allowed", False):
        logger.error(
            f"version_blocked:{version_resp.get('message', 'unknown')}",
            extra={"event": state.value},
        )
        return 1

    print("=== RTS Login ===")
    state = AuthState.SHOW_LOGIN
    action = input("Type 'login' or 'register': ").strip().lower()
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if action == "register":
        reg = api.register(username=username, password=password)
        if reg.get("error"):
            logger.error(f"register_failed:{reg['error']}", extra={"event": "register"})
            return 1

    state = AuthState.AUTHENTICATE
    auth = api.login(username=username, password=password)
    if auth.get("error"):
        logger.error(f"login_failed:{auth['error']}", extra={"event": state.value})
        return 1

    creds = SessionCredentials(
        access_token=auth["access_token"],
        refresh_token=auth["refresh_token"],
        access_expires_at=auth["access_expires_at"],
        refresh_expires_at=auth["refresh_expires_at"],
    )

    state = AuthState.STORE_SESSION
    sessions.save(creds)

    state = AuthState.AUTHENTICATED
    me = api.me(creds.access_token)
    if me.get("error"):
        logger.error(f"me_failed:{me['error']}", extra={"event": state.value})
        return 1

    state = AuthState.MAIN_MENU
    print(f"Welcome {me['username']}! Entered main menu shell.")
    print("Type 'logout' to end session.")
    if input("> ").strip().lower() == "logout":
        state = AuthState.LOGOUT
        api.logout(creds.access_token)
        sessions.clear()
        print("Logged out.")

    state = AuthState.EXIT
    logger.info("client_exit", extra={"event": state.value})
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/client.dev.json")
    args = parser.parse_args()
    raise SystemExit(run(args.config))
