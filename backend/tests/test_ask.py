import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ask_returns_answer_and_sources(client: AsyncClient):
    await client.post(
        "/documents",
        json={
            "title": "Refund Policy",
            "content": "Customers may request a refund within 30 days of purchase.",
        },
    )
    resp = await client.post(
        "/ask",
        json={"question": "How long do I have to request a refund?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"]
    assert data["mode"] == "mock"
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["title"] == "Refund Policy"


@pytest.mark.asyncio
async def test_ask_empty_knowledge_base(client: AsyncClient):
    resp = await client.post("/ask", json={"question": "Anything about refunds?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "couldn't find" in data["answer"].lower()
    assert data["sources"] == []
