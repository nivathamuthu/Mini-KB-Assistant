from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.dependencies import get_embedding_provider, get_llm_provider
from app.rate_limit import enforce_ask_rate_limit
from app.schemas import AskRequest, AskResponse
from app.services.embeddings import EmbeddingProvider
from app.services.llm import LLMProvider
from app.services.rag import ask_question

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(enforce_ask_rate_limit)])
async def ask(
    body: AskRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> AskResponse:
    return await ask_question(session, body.question, settings, embedding_provider, llm_provider)
