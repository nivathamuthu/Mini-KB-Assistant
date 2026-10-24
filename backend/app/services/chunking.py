from __future__ import annotations

import re

from app.config import Settings


def split_text(text: str, settings: Settings) -> list[str]:
    """Paragraph/sentence-aware recursive splitter with overlap."""
    size = settings.chunk_size
    overlap = settings.chunk_overlap
    if overlap >= size:
        overlap = max(0, size // 4)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []

    def push_piece(piece: str) -> None:
        piece = piece.strip()
        if piece:
            chunks.append(piece)

    def split_long(segment: str) -> list[str]:
        if len(segment) <= size:
            return [segment]
        sentences = re.split(r"(?<=[.!?])\s+", segment)
        parts: list[str] = []
        buf = ""
        for sent in sentences:
            if not sent:
                continue
            candidate = f"{buf} {sent}".strip() if buf else sent
            if len(candidate) <= size:
                buf = candidate
            else:
                if buf:
                    parts.append(buf)
                if len(sent) <= size:
                    buf = sent
                else:
                    for i in range(0, len(sent), size):
                        parts.append(sent[i : i + size])
                    buf = ""
        if buf:
            parts.append(buf)
        return parts

    for para in paragraphs:
        if len(para) <= size:
            push_piece(para)
        else:
            for part in split_long(para):
                push_piece(part)

    if not chunks:
        return []

    if overlap <= 0 or len(chunks) == 1:
        return chunks

    merged: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = merged[-1]
        tail = prev[-overlap:] if len(prev) > overlap else prev
        merged.append(f"{tail} {chunks[i]}".strip())
    return merged
