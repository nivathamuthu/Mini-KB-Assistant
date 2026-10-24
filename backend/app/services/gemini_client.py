from __future__ import annotations

import httpx

from app.config import Settings
from app.errors import ServiceUnavailableError


def require_gemini_api_key(settings: Settings) -> str:
    if not settings.gemini_api_key or not settings.gemini_api_key.strip():
        raise ServiceUnavailableError(
            "Google/Gemini API key is not configured (set GOOGLE_API_KEY or GEMINI_API_KEY in .env)."
        )
    return settings.gemini_api_key.strip()


def build_gemini_client(settings: Settings) -> httpx.AsyncClient:
    require_gemini_api_key(settings)
    return httpx.AsyncClient(
        base_url=settings.gemini_base_url.rstrip("/"),
        timeout=settings.upstream_timeout_seconds,
    )


def gemini_params(settings: Settings) -> dict[str, str]:
    return {"key": require_gemini_api_key(settings)}
