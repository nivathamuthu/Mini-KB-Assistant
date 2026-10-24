from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import Chunk, Document


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    title: str
    chunk_index: int
    text: str
    score: float


async def retrieve_top_k(
    session: AsyncSession,
    query_embedding: list[float],
    settings: Settings,
) -> list[RetrievedChunk]:
    distance = Chunk.embedding.cosine_distance(query_embedding)
    score_expr = (1 - distance).label("score")
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Document.title,
            Chunk.chunk_index,
            Chunk.text,
            score_expr,
        )
        .join(Document, Document.id == Chunk.document_id)
        .order_by(distance)
        .limit(settings.top_k)
    )
    result = await session.execute(stmt)
    rows = result.all()
    chunks: list[RetrievedChunk] = []
    for row in rows:
        score = float(row.score)
        if score < settings.min_relevance_score:
            continue
        chunks.append(
            RetrievedChunk(
                chunk_id=row.id,
                document_id=row.document_id,
                title=row.title,
                chunk_index=row.chunk_index,
                text=row.text,
                score=score,
            )
        )
    return chunks
