from __future__ import annotations

import hashlib
import math
import re
import random
from typing import Protocol

import httpx

from app.config import Settings
from app.errors import ServiceUnavailableError, UpstreamError, UpstreamTimeoutError
from app.services.gemini_client import build_gemini_client, gemini_params
from app.services.local_embeddings import LocalEmbeddingProvider


class EmbeddingProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class MockEmbeddingProvider:
    def __init__(self, settings: Settings) -> None:
        self.dim = settings.embedding_dim

    def _vector_for(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"[a-z0-9]+", text.lower()) or ["empty"]
        for tok in tokens:
            idx = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector_for(text)


class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        if not settings.openai_api_key:
            raise ServiceUnavailableError("OpenAI API key is not configured.")
        self.settings = settings
        self._client = client or httpx.AsyncClient(
            base_url=settings.openai_base_url,
            timeout=settings.upstream_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request_embeddings(self, inputs: list[str]) -> list[list[float]]:
        payload = {"model": self.settings.embedding_model, "input": inputs}
        last_exc: Exception | None = None
        for attempt in range(self.settings.upstream_max_retries + 1):
            try:
                resp = await self._client.post("/embeddings", json=payload)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt >= self.settings.upstream_max_retries:
                    raise UpstreamTimeoutError() from exc
                await _backoff_sleep(attempt)
                continue
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt >= self.settings.upstream_max_retries:
                    raise UpstreamError("Could not reach embedding service.") from exc
                await _backoff_sleep(attempt)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "60"))
                raise UpstreamError(
                    "Embedding provider rate limited.",
                    status_code=503,
                    headers={"Retry-After": str(retry_after)},
                )
            if resp.status_code >= 500:
                if attempt >= self.settings.upstream_max_retries:
                    raise UpstreamError("Embedding provider error.")
                await _backoff_sleep(attempt)
                continue
            if resp.status_code >= 400:
                raise UpstreamError("Embedding provider rejected the request.", status_code=502)

            data = resp.json()
            items = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in items]

        raise UpstreamError("Embedding request failed.") from last_exc

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._request_embeddings(texts)

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self._request_embeddings([text])
        return vectors[0]


class GeminiEmbeddingProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = client or build_gemini_client(settings)
        self._owns_client = client is None
        self._model = settings.gemini_embedding_model
        if not self._model.startswith("models/"):
            self._model = f"models/{self._model}"

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _embed_one(self, text: str) -> list[float]:
        payload = {
            "model": self._model,
            "content": {"parts": [{"text": text}]},
        }
        path = f"/{self._model}:embedContent"
        last_exc: Exception | None = None
        for attempt in range(self.settings.upstream_max_retries + 1):
            try:
                resp = await self._client.post(
                    path,
                    params=gemini_params(self.settings),
                    json=payload,
                )
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt >= self.settings.upstream_max_retries:
                    raise UpstreamTimeoutError() from exc
                await _backoff_sleep(attempt)
                continue
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt >= self.settings.upstream_max_retries:
                    raise UpstreamError("Could not reach Gemini embedding service.") from exc
                await _backoff_sleep(attempt)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "60"))
                raise UpstreamError(
                    "Gemini embedding rate limited.",
                    status_code=503,
                    headers={"Retry-After": str(retry_after)},
                )
            if resp.status_code >= 500:
                if attempt >= self.settings.upstream_max_retries:
                    raise UpstreamError("Gemini embedding service error.")
                await _backoff_sleep(attempt)
                continue
            if resp.status_code >= 400:
                raise UpstreamError("Gemini rejected the embedding request.", status_code=502)

            data = resp.json()
            embedding = data.get("embedding") or {}
            values = embedding.get("values")
            if not values:
                raise UpstreamError("Gemini returned an empty embedding.")
            return [float(v) for v in values]

        raise UpstreamError("Gemini embedding request failed.") from last_exc

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self._embed_one(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return await self._embed_one(text)


async def _backoff_sleep(attempt: int) -> None:
    import asyncio

    base = 0.25 * (2**attempt)
    jitter = random.uniform(0, 0.25)
    await asyncio.sleep(base + jitter)


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.uses_local_embeddings:
        try:
            return LocalEmbeddingProvider(settings)
        except ServiceUnavailableError:
            if settings.llm_provider_name == "gemini" and settings.gemini_api_key:
                import logging

                logging.getLogger(__name__).warning(
                    "EMBED_MODEL configured but local runtime unavailable; "
                    "falling back to Gemini API embeddings (use EMBEDDING_DIM=768)."
                )
                return GeminiEmbeddingProvider(settings)
            raise

    name = settings.provider_name
    if name == "mock":
        return MockEmbeddingProvider(settings)
    if name == "openai":
        return OpenAIEmbeddingProvider(settings)
    if name == "gemini":
        return GeminiEmbeddingProvider(settings)
    raise ServiceUnavailableError(
        f"Unknown LLM_PROVIDER/PROVIDER '{settings.llm_provider or settings.provider}'. "
        "Use mock, openai, or google/gemini, or set EMBED_MODEL for local vectors."
    )
