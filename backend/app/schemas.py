from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.config import get_settings


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        settings = get_settings()
        if not v:
            raise ValueError("Title cannot be empty.")
        if len(v) > settings.max_title_chars:
            raise ValueError(f"Title exceeds maximum length of {settings.max_title_chars} characters.")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        settings = get_settings()
        if not v:
            raise ValueError("Content cannot be empty.")
        if len(v) > settings.max_doc_chars:
            raise ValueError(f"Content exceeds maximum length of {settings.max_doc_chars} characters.")
        return v


class DocumentCreateResponse(BaseModel):
    document_id: UUID
    status: str = "indexed"
    chunk_count: int


class DocumentListItem(BaseModel):
    document_id: UUID
    title: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]
    total: int
    limit: int
    offset: int


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)

    @field_validator("question", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        settings = get_settings()
        if not v:
            raise ValueError("Question cannot be empty.")
        if len(v) > settings.max_question_chars:
            raise ValueError(
                f"Question exceeds maximum length of {settings.max_question_chars} characters."
            )
        return v


class SourceItem(BaseModel):
    document_id: UUID
    title: str
    chunk_index: int
    snippet: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    mode: str


class HealthResponse(BaseModel):
    status: str
    mode: str
