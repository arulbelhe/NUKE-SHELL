from __future__ import annotations

import threading
from collections import defaultdict, deque
from time import time

from .config import settings


class LoginRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time()
        window_start = now - settings.login_attempt_window_seconds
        with self._lock:
            bucket = self._attempts[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= settings.login_attempt_limit:
                return False
            bucket.append(now)
            return True


login_rate_limiter = LoginRateLimiter()
