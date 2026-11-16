from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from app.core.exceptions import NovaAppError


class SlidingWindowRateLimiter:
    """Thread-safe in-process sliding-window rate limiter for auth endpoints.

    Note: In multi-instance Cloud Run deployments, pair with Cloud Armor / edge
    rate limiting or a shared store if global cross-instance quotas are required.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, *, max_attempts: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_attempts:
                raise NovaAppError(
                    code="rate_limit_exceeded",
                    message="Too many authentication attempts. Please wait and try again.",
                    status_code=429,
                )
            bucket.append(now)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


auth_rate_limiter = SlidingWindowRateLimiter()
