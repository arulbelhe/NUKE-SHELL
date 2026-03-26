from __future__ import annotations

from enum import Enum


class AuthState(str, Enum):
    BOOT = "boot"
    LOAD_CONFIG = "load_config"
    CHECK_NETWORK = "check_network"
    VERSION_CHECK = "version_check"
    SHOW_LOGIN = "show_login"
    AUTHENTICATE = "authenticate"
    STORE_SESSION = "store_session"
    AUTHENTICATED = "authenticated"
    MAIN_MENU = "main_menu"
    LOGOUT = "logout"
    EXIT = "exit"
