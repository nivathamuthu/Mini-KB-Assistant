import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque

from fastapi import Request

from app.config import get_settings
from app.errors import RateLimitedError


class RateLimiter(ABC):
    @abstractmethod
    async def check(self, client_key: str) -> None:
        """Raise RateLimitedError if the client exceeded the limit."""


class InMemorySlidingWindowRateLimiter(RateLimiter):
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, client_key: str) -> None:
        now = time.monotonic()
        async with self._lock:
            window = self._hits[client_key]
            cutoff = now - self.window_seconds
            while window and window[0] < cutoff:
                window.popleft()
            if len(window) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - window[0])) + 1)
                raise RateLimitedError(
                    f"Too many requests. Try again in {retry_after}s.",
                    retry_after=retry_after,
                )
            window.append(now)


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = InMemorySlidingWindowRateLimiter(settings.rate_limit_per_minute)
    return _rate_limiter


def client_key_from_request(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    if request.client:
        return f"ip:{request.client.host}"
    return "ip:unknown"


async def enforce_ask_rate_limit(request: Request) -> None:
    limiter = get_rate_limiter()
    key = client_key_from_request(request)
    await limiter.check(key)
