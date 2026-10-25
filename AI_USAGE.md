# AI usage disclosure

## Tools used

- **Cursor Agent (Claude)** — scaffolding the repo from `README_Assistant.md` and the coding challenge docx, implementing backend/frontend/tests, and drafting architecture notes.

## Where AI influenced the design

- Repository layout and phase ordering followed the provided README build plan.
- Provider abstraction (mock, OpenAI, Google Gemini), optional local BGE embeddings (`EMBED_MODEL`), standard error JSON shape, and in-memory sliding-window rate limiter match the README’s suggested patterns.
- Mock embeddings use a simple bag-of-words hashing scheme so local demos retrieve overlapping terms without calling external APIs.
- Docker image installs CPU PyTorch + sentence-transformers and pre-downloads BGE-small for embedding/search when `EMBED_MODEL` is set.

## Reviewed / changed suggestion

**Suggestion (AI):** Use fully random hash-based embedding vectors for mock mode.

**Decision:** **Changed.** Pure random hashes per full string do not retrieve related chunks when the question shares words with a document, which breaks the demo ask flow. Replaced with normalized bag-of-words bucket vectors so shared tokens increase cosine similarity, while still keeping mock mode clearly non-production.

---

<!-- TODO (candidate): Add any additional tools you used personally and one honest example of a suggestion you rejected. -->
