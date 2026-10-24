from app.config import get_settings
from app.services.chunking import split_text


def test_chunking_respects_size_and_overlap():
    settings = get_settings()
    settings.chunk_size = 100
    settings.chunk_overlap = 20
    text = "Word. " * 80
    chunks = split_text(text, settings)
    assert chunks
    assert all(c.strip() for c in chunks)
    assert all(len(c) <= 150 for c in chunks)


def test_chunking_preserves_order():
    settings = get_settings()
    text = "Alpha paragraph.\n\nBeta paragraph.\n\nGamma paragraph."
    chunks = split_text(text, settings)
    joined = " ".join(chunks)
    assert "Alpha" in joined and "Beta" in joined and "Gamma" in joined
