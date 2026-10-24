import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.rate_limit import InMemorySlidingWindowRateLimiter


@pytest.mark.asyncio
async def test_rate_limit_returns_429_with_retry_after(client: AsyncClient):
    settings = get_settings()
    limit = settings.rate_limit_per_minute

    await client.post(
        "/documents",
        json={"title": "Policy", "content": "Refund within 30 days for all customers."},
    )

    last_status = 200
    for i in range(limit + 1):
        resp = await client.post(
            "/ask",
            json={"question": f"refund question {i}"},
            headers={"X-API-Key": "rate-limit-test-key"},
        )
        last_status = resp.status_code
        if resp.status_code == 429:
            assert "Retry-After" in resp.headers
            body = resp.json()
            assert body["error"]["code"] == "rate_limited"
            break

    assert last_status == 429


@pytest.mark.asyncio
async def test_sliding_window_limiter_unit():
    limiter = InMemorySlidingWindowRateLimiter(limit=2, window_seconds=60)
    await limiter.check("client-a")
    await limiter.check("client-a")
    from app.errors import RateLimitedError

    with pytest.raises(RateLimitedError) as exc_info:
        await limiter.check("client-a")
    assert exc_info.value.headers.get("Retry-After")
