"""Fail-closed access gate for potentially costly or privileged endpoints.

A single-process demo defence, not a distributed rate limiter or a billing cap.
It deliberately avoids IP-based identities, proxy headers and client-side secrets.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
import secrets
import threading
import time
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

LIVE_ENDPOINTS = frozenset({"/api/analyse", "/api/containment-probe"})
LOCAL_ENDPOINT = "/api/local-analyse"


@dataclass
class Slot:
    """Reservation released after endpoint completion, including exceptions."""
    limiter: "SlidingLimiter"
    released: bool = False

    def release(self) -> None:
        if not self.released:
            with self.limiter._lock:
                if not self.released:
                    self.limiter._active -= 1
                    self.released = True


class SlidingLimiter:
    """Process-wide rolling limits with a concurrency bound.

    This is intentionally conservative: failed admitted requests still count.
    Multiple Uvicorn workers/replicas each have an independent counter;
    public multi-instance deployments need an external shared quota and
    provider-side billing alerts/controls as well.
    """

    def __init__(self, *, per_window: int, window_seconds: int,
                 per_day: int, max_active: int, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._recent: deque[float] = deque()
        self._daily: deque[float] = deque()
        self._active = 0
        self.per_window = per_window
        self.window_seconds = window_seconds
        self.per_day = per_day
        self.max_active = max_active

    def reserve(self) -> tuple[Slot | None, int]:
        with self._lock:
            now = self._clock()
            while self._recent and now - self._recent[0] >= self.window_seconds:
                self._recent.popleft()
            while self._daily and now - self._daily[0] >= 86_400:
                self._daily.popleft()
            if self._active >= self.max_active:
                return None, 2
            if len(self._recent) >= self.per_window:
                return None, max(1, int(self.window_seconds - (now - self._recent[0])) + 1)
            if len(self._daily) >= self.per_day:
                return None, max(1, int(86_400 - (now - self._daily[0])) + 1)
            self._recent.append(now)
            self._daily.append(now)
            self._active += 1
            return Slot(self), 0

    def reset_for_tests(self) -> None:
        """Only use in isolated automated tests; not exposed via HTTP."""
        with self._lock:
            self._recent.clear()
            self._daily.clear()
            self._active = 0


# All live Docker and inference endpoints share a very small quota.
# Quotas are request counts, NOT a USD billing cap.
live_limiter = SlidingLimiter(per_window=4, window_seconds=3_600, per_day=10, max_active=1)
local_limiter = SlidingLimiter(per_window=60, window_seconds=60, per_day=500, max_active=2)


def _error(code: int, message: str, retry: int | None = None) -> JSONResponse:
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if retry is not None:
        headers["Retry-After"] = str(retry)
    return JSONResponse(status_code=code, content={"detail": message}, headers=headers)


def _authorised(request: Request) -> bool:
    secret = os.getenv("EXCEPTIONFORGE_ACCESS_TOKEN", "")
    if len(secret) < 32 or not secret.isascii() or any(x.isspace() for x in secret):
        return False
    # Never trust a token supplied by a query parameter or a browser cookie.
    supplied = request.headers.get("authorization", "")
    prefix = "Bearer "
    return supplied.startswith(prefix) and secrets.compare_digest(supplied[len(prefix):], secret)


async def access_middleware(request: Request, call_next):
    """Before body parsing or API calls, require live opt-in and a server-held token."""
    path = request.url.path
    if request.method != "POST" or path not in LIVE_ENDPOINTS | {LOCAL_ENDPOINT}:
        return await call_next(request)

    if path in LIVE_ENDPOINTS:
        if os.getenv("EXCEPTIONFORGE_ENABLE_LIVE", "").lower() != "true":
            return _error(503, "Live Vultr and Docker operations are disabled by the server operator.")
        secret = os.getenv("EXCEPTIONFORGE_ACCESS_TOKEN", "")
        if len(secret) < 32 or not secret.isascii() or any(x.isspace() for x in secret):
            return _error(503, "Live access token is not safely configured on the server.")
        if not _authorised(request):
            return _error(401, "Authorisation required for live operations.")
        if path == "/api/analyse" and not os.getenv("VULTR_INFERENCE_API_KEY", ""):
            return _error(503, "Vultr Inference key missing. Live agent run NOT attempted")
        limiter = live_limiter
    else:
        # Local demo remains usable without Vultr or credentials.
        limiter = local_limiter

    slot, retry = limiter.reserve()
    if slot is None:
        return _error(429, "Request limit or concurrency limit reached. Retry later.", retry)
    try:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    finally:
        slot.release()
