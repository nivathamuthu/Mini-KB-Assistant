from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import Question
from app.schemas import AskResponse, SourceItem
from app.services.embeddings import EmbeddingProvider
from app.services.llm import LLMProvider
from app.services.retrieval import retrieve_top_k

NOT_FOUND_ANSWER = (
    "I couldn't find this in the knowledge base based on the indexed articles."
)


async def ask_question(
    session: AsyncSession,
    question: str,
    settings: Settings,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
) -> AskResponse:
    started = time.perf_counter()
    mode = settings.response_mode

    query_vec = await embedding_provider.embed_query(question)
    chunks = await retrieve_top_k(session, query_vec, settings)

    if not chunks:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await _save_question(session, question, NOT_FOUND_ANSWER, [], latency_ms)
        return AskResponse(answer=NOT_FOUND_ANSWER, sources=[], mode=mode)

    answer = await llm_provider.generate_answer(question, chunks)
    sources = [
        SourceItem(
            document_id=ch.document_id,
            title=ch.title,
            chunk_index=ch.chunk_index,
            snippet=_snippet(ch.text),
            score=round(ch.score, 4),
        )
        for ch in chunks
    ]
    latency_ms = int((time.perf_counter() - started) * 1000)
    await _save_question(
        session,
        question,
        answer,
        [str(ch.chunk_id) for ch in chunks],
        latency_ms,
    )
    return AskResponse(answer=answer, sources=sources, mode=mode)


def _snippet(text: str, max_len: int = 240) -> str:
    t = " ".join(text.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


async def _save_question(
    session: AsyncSession,
    question: str,
    answer: str,
    chunk_ids: list[str],
    latency_ms: int,
) -> None:
    row = Question(
        question=question,
        answer=answer,
        source_chunk_ids=chunk_ids,
        latency_ms=latency_ms,
    )
    session.add(row)
    await session.flush()
