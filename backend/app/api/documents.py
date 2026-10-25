from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.dependencies import get_embedding_provider
from app.models import Chunk, Document
from app.schemas import (
    DocumentCreate,
    DocumentCreateResponse,
    DocumentListItem,
    DocumentListResponse,
)
from app.services.embeddings import EmbeddingProvider
from app.services.indexing import chunk_texts_for_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentCreateResponse, status_code=201)
async def create_document(
    body: DocumentCreate,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> DocumentCreateResponse:
    pieces = chunk_texts_for_document(body.title, body.content, settings)

    doc = Document(title=body.title, content=body.content)
    session.add(doc)
    await session.flush()

    vectors = await embedding_provider.embed_texts(pieces)
    for idx, (piece, vec) in enumerate(zip(pieces, vectors, strict=True)):
        session.add(
            Chunk(
                document_id=doc.id,
                chunk_index=idx,
                text=piece,
                embedding=vec,
            )
        )
    await session.flush()

    return DocumentCreateResponse(document_id=doc.id, chunk_count=len(pieces))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    total = await session.scalar(select(func.count()).select_from(Document)) or 0
    result = await session.execute(
        select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
    )
    docs = result.scalars().all()
    items = [
        DocumentListItem(document_id=d.id, title=d.title, created_at=d.created_at) for d in docs
    ]
    return DocumentListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/reindex", status_code=200)
async def reindex_documents(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> dict[str, int]:
    """Re-chunk and re-embed all documents (needed after changing EMBED_MODEL or provider)."""
    result = await session.execute(select(Document).order_by(Document.created_at.asc()))
    docs = result.scalars().all()
    updated = 0
    chunks_total = 0
    for doc in docs:
        await session.execute(
            Chunk.__table__.delete().where(Chunk.document_id == doc.id)
        )
        pieces = chunk_texts_for_document(doc.title, doc.content, settings)
        vectors = await embedding_provider.embed_texts(pieces)
        for idx, (piece, vec) in enumerate(zip(pieces, vectors, strict=True)):
            session.add(
                Chunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    text=piece,
                    embedding=vec,
                )
            )
        updated += 1
        chunks_total += len(pieces)
    await session.flush()
    return {"documents_reindexed": updated, "chunks_indexed": chunks_total}
