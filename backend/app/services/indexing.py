from app.config import Settings
from app.services.chunking import split_text


def chunk_texts_for_document(title: str, content: str, settings: Settings) -> list[str]:
    """Split content and prefix each chunk with title for search and display."""
    pieces = split_text(content, settings)
    if not pieces:
        pieces = [content.strip()]
    titled: list[str] = []
    for piece in pieces:
        titled.append(f"Title: {title.strip()}\n\n{piece.strip()}")
    return titled
