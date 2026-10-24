from functools import lru_cache

from app.config import Settings, get_settings
from app.services.embeddings import EmbeddingProvider, build_embedding_provider
from app.services.llm import LLMProvider, build_llm_provider


@lru_cache
def get_embedding_provider_cached() -> EmbeddingProvider:
    return build_embedding_provider(get_settings())


@lru_cache
def get_llm_provider_cached() -> LLMProvider:
    return build_llm_provider(get_settings())


def get_embedding_provider() -> EmbeddingProvider:
    return get_embedding_provider_cached()


def get_llm_provider() -> LLMProvider:
    return get_llm_provider_cached()


def clear_provider_cache() -> None:
    get_settings.cache_clear()
    get_embedding_provider_cached.cache_clear()
    get_llm_provider_cached.cache_clear()
