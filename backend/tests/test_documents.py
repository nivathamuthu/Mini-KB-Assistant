import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_documents(client: AsyncClient):
    create = await client.post(
        "/documents",
        json={"title": "Refund Policy", "content": "Customers may request a refund within 30 days."},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["chunk_count"] >= 1
    doc_id = body["document_id"]

    listing = await client.get("/documents?limit=10&offset=0")
    assert listing.status_code == 200
    data = listing.json()
    assert data["total"] >= 1
    assert any(item["document_id"] == doc_id for item in data["items"])


@pytest.mark.asyncio
async def test_reject_empty_title(client: AsyncClient):
    resp = await client.post("/documents", json={"title": "  ", "content": "Some content"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_oversized_content(client: AsyncClient):
    settings_content = "x" * 200_001
    resp = await client.post(
        "/documents",
        json={"title": "Big", "content": settings_content},
    )
    assert resp.status_code == 422
