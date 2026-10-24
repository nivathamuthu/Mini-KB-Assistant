# Mini Knowledge Assistant

A small RAG (retrieval-augmented generation) service for an internal support team. Users add knowledge articles, ask questions in natural language, and get a grounded answer with source references.

- **Backend:** Python 3.11+, FastAPI (async), PostgreSQL + pgvector
- **Frontend:** React (Vite) + TypeScript
- **LLM / Embeddings:** pluggable provider (OpenAI-compatible) with a **mock fallback** so the app runs with no API key
- **Effort target:** ~4–6 hours, vertical slice, clear trade-offs

> **How to use this file with Cursor:** Put this README in an empty repo, open the folder in Cursor, and follow [Section 12 – Cursor Build Plan](#12-cursor-build-plan). Each phase has a ready-to-paste prompt. Section 13 contains the rules to save as `.cursorrules` (or `.cursor/rules/project.mdc`).

---

## 1. What this project does

1. **Ingest** a document (`POST /documents`): validate, persist, chunk, embed, index.
2. **List** documents (`GET /documents`): paginated metadata.
3. **Ask** a question (`POST /ask`): embed the question, vector-search top-k chunks, generate a grounded answer, return sources.
4. **UI:** React page to ask questions and see loading, answer, sources, and errors (plus an optional add/list documents view).

---

## 2. Requirements checklist (from the challenge)

| Area | Requirement | Status |
| --- | --- | --- |
| API | `POST /documents`, `GET /documents`, `POST /ask` | ☐ |
| Validation | Reject empty / oversized input with 4xx and useful messages | ☐ |
| RAG | Chunking → embeddings → vector search → grounded generation → sources | ☐ |
| Fallback | Mock/local embeddings + LLM, clearly labelled as demo-only | ☐ |
| UI | Question box, Ask button, loading, answer, sources, error state | ☐ |
| Rate limit | `POST /ask` ≈ 20 req/min per client, HTTP 429 + `Retry-After` | ☐ |
| Errors | Timeouts, bounded retries, upstream 429 handling, no secret/stack leaks | ☐ |
| Tests | Focused tests for important API behaviour | ☐ |
| Docs | README, ARCHITECTURE.md (incl. 10K/100K/1M discussion), AI_USAGE.md | ☐ |
| Git | ≥ 3 meaningful commits, no secrets / build artifacts | ☐ |

---

## 3. Repository layout

```
mini-knowledge-assistant/
├── README.md
├── ARCHITECTURE.md
├── AI_USAGE.md
├── docker-compose.yml          # postgres (pgvector) [+ optional redis]
├── .env.example
├── .gitignore
├── backend/
│   ├── pyproject.toml          # or requirements.txt
│   ├── alembic.ini             # optional; or create tables on startup
│   ├── app/
│   │   ├── main.py             # app factory, routers, middleware, exception handlers
│   │   ├── config.py           # pydantic-settings, env-driven
│   │   ├── logging_config.py   # structured logging, request IDs
│   │   ├── db.py               # async engine/session, pgvector setup
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── errors.py           # custom exceptions + handlers
│   │   ├── rate_limit.py       # sliding-window limiter (in-memory, Redis-ready)
│   │   ├── api/
│   │   │   ├── documents.py
│   │   │   ├── ask.py
│   │   │   └── health.py
│   │   └── services/
│   │       ├── chunking.py
│   │       ├── embeddings.py   # EmbeddingProvider (OpenAI + Mock)
│   │       ├── llm.py          # LLMProvider (OpenAI + Mock)
│   │       ├── retrieval.py    # vector search
│   │       └── rag.py          # orchestrates ask flow
│   └── tests/
│       ├── conftest.py
│       ├── test_documents.py
│       ├── test_ask.py
│       ├── test_rate_limit.py
│       └── test_chunking.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api.ts              # typed fetch client
        ├── components/
        │   ├── AskForm.tsx
        │   ├── AnswerView.tsx
        │   ├── SourceList.tsx
        │   ├── ErrorBanner.tsx
        │   └── DocumentsPanel.tsx   # optional add + list
        └── styles.css
```

---

## 4. Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker + Docker Compose (for PostgreSQL with pgvector)
- *(Optional)* An OpenAI-compatible API key. **Not required** — set `PROVIDER=mock` to run fully offline.

---

## 5. Configuration

Copy `.env.example` to `.env` (never commit `.env`).

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://kb:kb@localhost:5432/kb` | Async Postgres URL |
| `PROVIDER` | `mock` | `mock` or `openai` |
| `OPENAI_API_KEY` | – | Required only if `PROVIDER=openai` |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible endpoint |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `EMBEDDING_DIM` | `1536` (`384` for mock) | Must match the vector column |
| `LLM_MODEL` | `gpt-4o-mini` | Chat model |
| `CHUNK_SIZE` | `800` | Target chunk size (characters) |
| `CHUNK_OVERLAP` | `120` | Overlap between chunks |
| `TOP_K` | `4` | Chunks retrieved per question |
| `MAX_DOC_CHARS` | `200000` | Max document size |
| `MAX_TITLE_CHARS` | `200` | Max title length |
| `MAX_QUESTION_CHARS` | `1000` | Max question length |
| `RATE_LIMIT_PER_MINUTE` | `20` | Per-client limit on `POST /ask` |
| `UPSTREAM_TIMEOUT_SECONDS` | `20` | Timeout for embedding/LLM calls |
| `UPSTREAM_MAX_RETRIES` | `2` | Bounded retries with backoff + jitter |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |
| `LOG_LEVEL` | `INFO` | Logging level |

> **Mock mode is a demo fallback only.** Mock embeddings are deterministic hash-based vectors and the mock LLM is extractive (it quotes the top chunks). Neither reflects production quality. The API returns `"mode": "mock"` in `/health` and logs a startup warning so this is never silent.

---

## 6. Setup and run

```bash
# 1. Start Postgres (pgvector)
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                                # or: pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                                            # http://localhost:5173
```

- API docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health

### Run tests

```bash
cd backend && pytest -q
cd frontend && npm test        # optional
```

---

## 7. API reference

### `POST /documents`
Request:
```json
{ "title": "Refund Policy", "content": "Customers may request a refund within 30 days..." }
```
Response `201`:
```json
{ "document_id": "3f0c...", "status": "indexed", "chunk_count": 3 }
```
Errors: `422` invalid/empty/oversized input.

### `GET /documents?limit=20&offset=0`
Response `200`:
```json
{
  "items": [{ "document_id": "3f0c...", "title": "Refund Policy", "created_at": "2025-01-01T10:00:00Z" }],
  "total": 1, "limit": 20, "offset": 0
}
```

### `POST /ask`
Request:
```json
{ "question": "How long do I have to request a refund?" }
```
Response `200`:
```json
{
  "answer": "You can request a refund within 30 days of purchase.",
  "sources": [
    { "document_id": "3f0c...", "title": "Refund Policy", "chunk_index": 0, "snippet": "Customers may request a refund within 30 days...", "score": 0.83 }
  ],
  "mode": "mock | openai"
}
```
Errors: `422` invalid input · `429` rate limited (with `Retry-After`) · `502/503` upstream failure · `504` upstream timeout.

If no chunk passes the relevance threshold, return a `200` with a clear "I couldn't find this in the knowledge base" answer and an empty `sources` list (do not hallucinate).

### Standard error shape
```json
{ "error": { "code": "rate_limited", "message": "Too many requests. Try again in 12s.", "request_id": "a1b2..." } }
```
No stack traces, API keys, prompts, or connection strings in responses.

### Example `curl`
```bash
curl -X POST localhost:8000/documents -H "Content-Type: application/json" \
  -d '{"title":"Refund Policy","content":"Customers may request a refund within 30 days of purchase."}'

curl "localhost:8000/documents?limit=10&offset=0"

curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question":"How long do I have to request a refund?"}'
```

---

## 8. Design decisions (summary — details in `ARCHITECTURE.md`)

**Data model (PostgreSQL + pgvector)**

| Table | Key columns |
| --- | --- |
| `documents` | `id (uuid)`, `title`, `content`, `created_at` |
| `chunks` | `id`, `document_id (fk, cascade)`, `chunk_index`, `text`, `embedding vector(N)` — HNSW index with cosine ops |
| `questions` | `id`, `question`, `answer`, `source_chunk_ids`, `latency_ms`, `created_at` (history / analytics) |

**Chunking:** paragraph/sentence-aware recursive splitter, ~800 chars with ~120 overlap; each chunk keeps `document_id`, `title`, `chunk_index`.

**Retrieval:** cosine similarity via pgvector, top-k (default 4), minimum score threshold to avoid irrelevant context.

**Generation:** system prompt instructs the model to answer *only* from the provided context, say so if the answer is missing, and cite sources. Context is passed as delimited, numbered chunks (treated as data, not instructions, to reduce prompt-injection risk).

**Async:** `asyncpg` + SQLAlchemy async; `httpx.AsyncClient` (shared, pooled) for provider calls; no blocking calls in request handlers. Any CPU-heavy work (e.g. a local embedding model) goes through `run_in_executor`.

**Rate limiting:** sliding-window per client key (API key header if present, else client IP), default 20/min, in-memory for local use behind a `RateLimiter` interface so a Redis implementation can be swapped in for multi-instance deployments. Returns `429` with `Retry-After` computed from the oldest request in the window.

**Upstream resilience:** explicit timeouts; ≤ 2 retries with exponential backoff + jitter on timeouts/5xx; on upstream `429` honour the provider's `Retry-After`, do **not** retry-storm, and surface a `503` with `Retry-After` to the client while logging the real cause.

**Failure behaviour:** DB/vector store down → `503` "service temporarily unavailable"; LLM down → `502/503`, UI shows a friendly retry message; optionally fall back to returning the retrieved sources without a generated answer.

**Assumptions:** single tenant, no auth (client identified by IP/header), documents are plain text/markdown, knowledge base is small initially.

---

## 9. Scalability (summary — full discussion in `ARCHITECTURE.md`)

| Scale | First bottleneck | Evolution |
| --- | --- | --- |
| **10K concurrent** | LLM latency/quota, DB connections | Async I/O, request timeouts, connection pooling, multiple Uvicorn/Gunicorn workers, concurrency semaphore + circuit breaker around the LLM call |
| **100K concurrent** | Single-node limits, shared state | Horizontal scaling behind a load balancer, Redis-backed rate limiting, cache embeddings and frequent answers, queue/backpressure for ingestion, metrics/tracing/alerts |
| **1M concurrent** | Provider quota, vector search throughput | Split sync API traffic from background ingestion workers, independently scaled embedding/retrieval/LLM services, read replicas or a dedicated vector DB, partitioning/multi-region, graceful degradation (retrieval-only answers, cached answers) |

Assumptions to measure before deciding: p50/p95 LLM latency, tokens per request, cache hit rate, corpus size/growth, read-vs-write ratio, vector index recall vs. latency, and provider rate limits.

---

## 10. Testing strategy

- `test_documents.py` — create → list; empty title/content → 422; oversized content → 422; pagination.
- `test_ask.py` — end-to-end with mock providers; sources returned; empty KB returns a safe "not found" answer; upstream failure maps to the right 5xx.
- `test_rate_limit.py` — the 21st request in a minute returns `429` with `Retry-After`.
- `test_chunking.py` — chunk size/overlap bounds, no empty chunks, order preserved.
- Use a test database (or transaction rollbacks) and dependency overrides for providers — **tests never call real external APIs.**

---

## 11. Git workflow

Commit in meaningful steps (≥ 3), e.g.:

1. `feat: scaffold FastAPI app, config, DB models, docker-compose`
2. `feat: document ingestion with chunking, embeddings and pgvector index`
3. `feat: /ask RAG flow with mock + OpenAI providers`
4. `feat: rate limiting, error handling, timeouts and retries`
5. `feat: React UI (ask, answer, sources, errors)`
6. `test: API, chunking and rate-limit tests`
7. `docs: README, ARCHITECTURE, AI_USAGE`

Never commit `.env`, API keys, `node_modules`, `.venv`, build output, or large generated files.

---

## 12. Cursor Build Plan

Work through the phases in order. In Cursor, open Chat/Agent mode, paste the prompt for the phase, review the diff, run the checks, then commit.

### Phase 0 — Project rules
Create `.cursor/rules/project.mdc` (or `.cursorrules`) from [Section 13](#13-cursor-rules-file).

### Phase 1 — Scaffold
```
Read README.md fully. Scaffold the repo exactly as in "Repository layout":
- docker-compose.yml with a pgvector/pgvector:pg16 service (db kb/kb/kb, port 5432)
- .env.example from the Configuration table
- .gitignore (python, node, .env, build artifacts)
- backend with pyproject.toml (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pgvector,
  pydantic-settings, httpx, pytest, pytest-asyncio) and app/config.py, db.py, models.py,
  main.py with GET /health. Create tables + the vector extension on startup.
Do not implement features beyond scaffolding yet.
```
**Check:** `docker compose up -d db`, `uvicorn app.main:app`, `GET /health` returns 200. **Commit.**

### Phase 2 — Ingestion
```
Implement POST /documents and GET /documents per README section 7.
- Pydantic schemas with length validation (MAX_TITLE_CHARS, MAX_DOC_CHARS), strip whitespace, reject empty.
- services/chunking.py: recursive paragraph/sentence-aware splitter using CHUNK_SIZE and CHUNK_OVERLAP.
- services/embeddings.py: EmbeddingProvider protocol; MockEmbeddingProvider (deterministic hash-based,
  EMBEDDING_DIM=384, normalized) and OpenAIEmbeddingProvider (httpx.AsyncClient, timeout, bounded retries).
- Persist document + chunks + embeddings in one transaction; HNSW cosine index on chunks.embedding.
- GET /documents with limit/offset (max limit 100) returning total.
Add tests for validation, creation, listing and chunking.
```
**Check:** `pytest -q` passes. **Commit.**

### Phase 3 — RAG `/ask`
```
Implement POST /ask.
- services/retrieval.py: cosine similarity top-k query via pgvector, min score threshold.
- services/llm.py: LLMProvider protocol; MockLLMProvider (extractive: composes an answer from top chunks,
  labelled mock) and OpenAILLMProvider (httpx async, timeout, bounded retries, honour upstream 429/Retry-After).
- services/rag.py: embed question -> retrieve -> build grounded prompt (numbered, delimited context,
  "answer only from context; say you don't know otherwise") -> generate -> return answer + sources.
- Save each Q&A to the questions table (with latency_ms).
- If nothing relevant is retrieved, return a safe "not found" answer with empty sources without calling the LLM.
- Response includes `mode` (mock/openai).
Add tests using the mock providers via FastAPI dependency overrides.
```
**Check:** add a doc, ask a question, answer + sources returned. **Commit.**

### Phase 4 — Reliability and protection
```
Add production-minded behaviour:
- errors.py + exception handlers producing the standard error shape with request_id; never leak stack traces,
  keys, prompts or connection strings.
- Middleware that assigns a request_id and logs method, path, status, latency (structured logging).
- rate_limit.py: RateLimiter interface + in-memory sliding-window implementation (RATE_LIMIT_PER_MINUTE),
  applied as a dependency on POST /ask only. Return 429 with Retry-After and a JSON error body.
  Client key = X-API-Key header if present else client IP.
- Map failures: upstream timeout -> 504, upstream 5xx/connection -> 502, upstream 429 -> 503 with Retry-After,
  DB unavailable -> 503.
- CORS from CORS_ORIGINS.
Add tests for 429 + Retry-After and for upstream-failure mapping.
```
**Check:** 21st request in a minute returns 429. **Commit.**

### Phase 5 — React UI
```
Create the Vite + React + TypeScript app in /frontend.
- api.ts: typed client using VITE_API_URL (default http://localhost:8000); parse the standard error shape.
- AskForm (textarea, Ask button disabled while loading/empty, Enter+Ctrl submits).
- Loading state (spinner/"Thinking..."), AnswerView, SourceList (title, snippet, score),
  ErrorBanner (friendly messages for 429 with retry-after countdown, 5xx, network error, no-answer case).
- Optional DocumentsPanel: add document form + paginated list.
- Minimal, clean CSS; accessible labels and aria-live for status/errors.
```
**Check:** full flow works in the browser against the running backend. **Commit.**

### Phase 6 — Documentation
```
Write ARCHITECTURE.md covering: data model; service boundaries (API, persistence, vector search, embedding
service, LLM provider); async behaviour and how the event loop is never blocked; operational concerns
(logging, config/secrets, timeouts, retries, monitoring/metrics); failure behaviour (what the user sees);
rate-limiting choice incl. Retry-After and upstream 429 handling; and the 10K / 100K / 1M scalability
discussion with the expected first bottleneck at each level and the assumptions to measure.
Include a simple Mermaid architecture diagram.
Write AI_USAGE.md (tools used, where AI shaped the design, and one concrete suggestion I reviewed/changed/rejected
and why — leave a clearly marked placeholder for me to fill in honestly).
Update README with final run/test instructions and tick the checklist.
```
**Commit.**

### Phase 7 — Final review
```
Review the whole repo against the "Requirements checklist" in README.md. List anything missing, any secret or
generated file that should not be committed, any blocking call in async code, and any error path that leaks
internals. Fix what you find.
```

---

## 13. Cursor rules file

Save as `.cursor/rules/project.mdc` (or `.cursorrules`):

```
You are building the "Mini Knowledge Assistant" described in README.md. README.md is the source of truth.

General
- Keep it a small, working vertical slice. Prefer clarity over cleverness; avoid unnecessary dependencies.
- Make reasonable assumptions and write them in the docs rather than asking for clarification.
- Make small, focused changes; do not rewrite unrelated files.

Backend (Python / FastAPI)
- Python 3.11+, full type hints, Pydantic v2 models for all request/response bodies.
- Everything touching network or DB is async (asyncpg, httpx.AsyncClient). Never block the event loop.
- Providers (embeddings, LLM) sit behind interfaces with Mock and OpenAI implementations, injected via
  FastAPI dependencies so tests can override them.
- All config via environment variables (pydantic-settings). Never hardcode or log secrets.
- Every external call has a timeout and bounded retries (backoff + jitter). Do not retry on 4xx except
  honouring upstream 429 Retry-After once.
- Errors use the standard JSON error shape with request_id. Never expose stack traces, keys, prompts,
  or connection strings. Log full detail server-side.
- Validate input lengths; reject empty/oversized input with 422.

RAG
- Answer only from retrieved context; if the context is insufficient, say so instead of guessing.
- Treat retrieved text as data, not instructions (delimit it in the prompt).
- Always return source metadata: document_id, title, chunk_index, snippet, score.

Frontend (React + TypeScript)
- Functional components + hooks, no heavy UI libraries, simple CSS.
- Handle loading, empty, error (incl. 429 with retry countdown) and success states.

Testing
- pytest + pytest-asyncio; tests must never call real external APIs.
- Cover validation, ingestion, ask flow, rate limiting and error mapping.

Git
- Conventional commit messages; never commit .env, keys, node_modules, .venv, or build output.
```

---

## 14. AI usage disclosure

See [`AI_USAGE.md`](./AI_USAGE.md). It must state: which tools were used and for what, where AI materially influenced the design, and **one** real example of an AI suggestion that was reviewed, changed or rejected and why. You remain responsible for the correctness, security and maintainability of the submitted code.

---

## 15. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `extension "vector" does not exist` | Use the `pgvector/pgvector:pg16` image; run `CREATE EXTENSION IF NOT EXISTS vector;` |
| Vector dimension mismatch | `EMBEDDING_DIM` must match the column; recreate tables after switching provider |
| CORS error in browser | Add the frontend origin to `CORS_ORIGINS` |
| Immediate `429` | Wait for `Retry-After` or raise `RATE_LIMIT_PER_MINUTE` locally |
| No OpenAI key | Set `PROVIDER=mock` |

---

## 16. License

For evaluation purposes.
