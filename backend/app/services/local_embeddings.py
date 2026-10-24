from __future__ import annotations

import asyncio
from functools import lru_cache

from app.config import Settings
from app.errors import ServiceUnavailableError


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ServiceUnavailableError(
            "Local embeddings require sentence-transformers. "
            'Install with: pip install -e ".[local]"'
        ) from exc
    return SentenceTransformer(model_name)


def _encode_sync(model_name: str, texts: list[str]) -> list[list[float]]:
    model = _load_model(model_name)
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


class LocalEmbeddingProvider:
    """CPU embeddings via Hugging Face sentence-transformers (e.g. BGE)."""

    def __init__(self, settings: Settings) -> None:
        if not settings.embed_model or not settings.embed_model.strip():
            raise ServiceUnavailableError("EMBED_MODEL is not configured.")
        self._model_name = settings.embed_model.strip()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _encode_sync, self._model_name, texts)

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]
