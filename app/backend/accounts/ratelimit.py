"""Minimal in-process rate limiting for the sensitive auth endpoints.

Fixed-window counters per (client IP, route tag), no external dependencies.
The API is served by uvicorn directly (no nginx in front), so request.client
is the real peer address. Limits reset on process restart — acceptable for
abuse damping (this is not billing-grade accounting).
"""
import threading
import time

from fastapi import HTTPException, Request

_lock = threading.Lock()
_windows = {}  # (ip, tag) -> [window_start, count]


def limit(tag: str, max_requests: int, per_seconds: int):
    """FastAPI dependency factory: 429 when the caller exceeds
    max_requests within per_seconds."""

    def dependency(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        key = (ip, tag)
        with _lock:
            window = _windows.get(key)
            if window is None or now - window[0] >= per_seconds:
                _windows[key] = [now, 1]
                # Opportunistic cleanup so the map cannot grow unbounded.
                if len(_windows) > 50000:
                    _windows.clear()
                    _windows[key] = [now, 1]
                return
            window[1] += 1
            if window[1] > max_requests:
                retry_after = int(per_seconds - (now - window[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests — try again shortly",
                    headers={"Retry-After": str(retry_after)},
                )

    return dependency
