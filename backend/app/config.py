from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = "postgresql+asyncpg://kb:kb@localhost:5432/kb"

    # Legacy single switch (mock | openai | gemini)
    provider: str = "mock"
    # Preferred LLM switch (google | openai | mock | gemini)
    llm_provider: str | None = Field(default=None, validation_alias="LLM_PROVIDER")

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"

    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 384
    embed_model: str | None = Field(default=None, validation_alias="EMBED_MODEL")

    llm_model: str = Field(default="", validation_alias="LLM_MODEL")

    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4
    min_relevance_score: float = 0.15

    max_doc_chars: int = 200_000
    max_title_chars: int = 200
    max_question_chars: int = 1000

    rate_limit_per_minute: int = 20
    upstream_timeout_seconds: float = 20.0
    upstream_max_retries: int = 2

    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def normalize_provider_fields(self) -> "Settings":
        if self.llm_model is not None:
            self.llm_model = self.llm_model.strip()
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_provider_name(self) -> str:
        raw = (self.llm_provider or self.provider or "mock").lower().strip()
        if raw == "google":
            return "gemini"
        return raw

    @property
    def provider_name(self) -> str:
        """Embedding/RAG provider when EMBED_MODEL is not set."""
        return self.llm_provider_name

    @property
    def uses_local_embeddings(self) -> bool:
        return bool(self.embed_model and self.embed_model.strip())

    @property
    def is_mock(self) -> bool:
        return self.llm_provider_name == "mock" and not self.uses_local_embeddings

    @property
    def chat_model(self) -> str:
        if self.llm_provider_name == "gemini":
            if self.llm_model:
                return self.llm_model
            return self.gemini_model
        if self.llm_provider_name == "openai":
            if self.llm_model:
                return self.llm_model
            return "gpt-4o-mini"
        return self.llm_model or self.gemini_model

    @property
    def response_mode(self) -> str:
        if self.llm_provider_name == "mock" and not self.uses_local_embeddings:
            return "mock"
        if self.llm_provider_name == "gemini":
            return "google" if (self.llm_provider or "").lower().strip() == "google" else "gemini"
        if self.llm_provider_name == "openai":
            return "openai"
        if self.uses_local_embeddings and self.llm_provider_name == "mock":
            return "local"
        return self.llm_provider_name


@lru_cache
def get_settings() -> Settings:
    return Settings()
