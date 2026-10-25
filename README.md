# Mini Knowledge Assistant

A small RAG (retrieval-augmented generation) service for an internal support team. Users add knowledge articles, ask questions in natural language, and get a grounded answer with source references.

- **Backend:** Python 3.11+, FastAPI (async), PostgreSQL + pgvector
- **Frontend:** React (Vite) + TypeScript
- **Embeddings:** local **BGE** (`EMBED_MODEL`) in Docker/local, or mock / OpenAI / Gemini API
- **LLM:** **Google Gemini** via `LLM_PROVIDER=google` and `GOOGLE_API_KEY` (same as Gemini API key), OpenAI, or **mock** demo mode

## Requirements checklist

| Area | Requirement | Status |
| --- | --- | --- |
| API | `POST /documents`, `GET /documents`, `POST /ask` | ☑ |
| Validation | Reject empty / oversized input with 4xx and useful messages | ☑ |
| RAG | Chunking → embeddings → vector search → grounded generation → sources | ☑ |
| Fallback | Mock embeddings + LLM, clearly labelled as demo-only | ☑ |
| UI | Question box, Ask button, loading, answer, sources, error state | ☑ |
| Rate limit | `POST /ask` ≈ 20 req/min per client, HTTP 429 + `Retry-After` | ☑ |
| Errors | Timeouts, bounded retries, upstream 429 handling, no secret/stack leaks | ☑ |
| Tests | Focused tests for important API behaviour | ☑ |
| Docs | README, ARCHITECTURE.md, AI_USAGE.md | ☑ |

## Prerequisites

- **Docker Desktop** (recommended: runs db + pgadmin + backend + frontend)
- Or: Python 3.11+, Node 18+, Docker only for Postgres

## Quick start (Docker — recommended)

1. Copy env file and add your Gemini key (never commit `.env`):

   ```powershell
   copy .env.example .env
   # Edit .env: GOOGLE_API_KEY=... and LLM_MODEL=gemini-3.5-flash-lite
   ```

2. Start the stack:

   ```powershell
   .\docker-up.ps1
   ```

   Or:

   ```powershell
   docker compose up -d --build
   ```

3. Open:

   | Service | URL |
   | --- | --- |
   | **UI** | http://localhost:5173 |
   | **API** | http://localhost:8001 |
   | **Swagger** | http://localhost:8001/docs |
   | **Health** | http://localhost:8001/health |
   | **pgAdmin** | http://localhost:5050 |

   Default API host port is **8001** (avoids clash with other apps on 8000).

4. In the UI: add a knowledge article → ask a question → review answer and sources.

**After changing `.env`**, recreate the backend so it picks up new values:

```powershell
docker compose up -d --force-recreate backend
```

Stop everything: `docker compose down`  
Remove DB data: `docker compose down -v` (then re-add documents)

## Local development (Python + Node on host)

```powershell
# 1. Database only (Postgres on host port 5433 by default)
docker compose up -d db

# 2. Backend — use DATABASE_URL with port 5433 when talking to Docker db from the host
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,local]"
copy ..\.env.example ..\.env
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- API: http://localhost:8000  
- UI: http://localhost:5173 (set `VITE_API_URL=http://localhost:8000` if needed)

## Configuration

Copy `.env.example` → `.env` at the repo root. **Never commit `.env`** (it is in `.gitignore`).

### Recommended setup (Gemini + local BGE)

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=your_key_from_google_ai_studio
LLM_MODEL=gemini-3.5-flash-lite
EMBED_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384
DATABASE_URL=postgresql+asyncpg://kb:kb@localhost:5433/kb
DB_HOST_PORT=5433
```

| Variable | Description |
| --- | --- |
| `LLM_PROVIDER` | `google` (Gemini chat), `openai`, or `mock` |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini API key for **answers** on `POST /ask` |
| `LLM_MODEL` | Chat model, e.g. `gemini-3.5-flash-lite` or `gemini-3.8-flash` |
| `EMBED_MODEL` | Local Hugging Face model for **search**; Docker image includes BGE |
| `EMBEDDING_DIM` | `384` (BGE-small), `768` (Gemini API embeddings), `1536` (OpenAI) |
| `DB_HOST_PORT` | Host port for Postgres (default **5433**; avoids Windows PostgreSQL on 5432) |
| `TOP_K` / `MIN_RELEVANCE_SCORE` | Retrieval tuning (default 4 / 0.15) |

Legacy: `PROVIDER=mock|openai|gemini` still works. Retired Gemini 2.x model IDs are auto-mapped to 3.x in config.

### Demo without API keys

```env
LLM_PROVIDER=mock
# Leave EMBED_MODEL unset for hash-based demo embeddings
EMBEDDING_DIM=384
```

## API reference

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/documents` | Add article (chunk + embed + index) |
| `GET` | `/documents` | List articles (paginated; see below) |
| `POST` | `/documents/reindex` | Re-chunk and re-embed **all** documents |
| `POST` | `/ask` | RAG question → answer + sources |
| `GET` | `/health` | Liveness + configured `mode` (see below) |

Interactive docs: **Swagger** at `/docs`.

### `GET /documents` — `limit` and `offset`

Pagination query parameters (newest first):

| Param | Default | Meaning |
| --- | --- | --- |
| `limit` | `20` | Max rows returned (1–100) |
| `offset` | `0` | How many rows to skip |

Example: `GET /documents?limit=10&offset=10` is the second page of 10. Response includes `items`, `total`, `limit`, and `offset`. List items expose `document_id`, `title`, and `created_at` (not full content).

### `GET /health` — `status` and `mode`

- **`status: "ok"`** — API is running (does not call Gemini).
- **`mode`** — reflects **configuration**, not a live API test:
  - **`google`** — `LLM_PROVIDER=google` (Gemini for chat); embeddings may still be local if `EMBED_MODEL` is set.
  - **`mock`**, **`openai`**, **`gemini`**, **`local`** — other provider combinations.

### `POST /documents/reindex`

Rebuilds the search index for every row in **`documents`**: deletes old **`chunks`**, re-splits text, re-embeds with the **current** embedding settings, inserts new vectors. Does **not** change article titles or content.

Call after changing `EMBED_MODEL`, embedding provider, or chunk settings. Restart the backend after `.env` changes, then reindex once. No request body.

### Examples (Docker API on port 8001)

```powershell
curl -X POST http://localhost:8001/documents -H "Content-Type: application/json" -d "{\"title\":\"Refund Policy\",\"content\":\"Customers may request a refund within 30 days.\"}"

curl "http://localhost:8001/documents?limit=10&offset=0"

curl -X POST http://localhost:8001/ask -H "Content-Type: application/json" -d "{\"question\":\"Explain the Refund Policy?\"}"

curl -X POST http://localhost:8001/documents/reindex

curl http://localhost:8001/health
```

## Data storage (PostgreSQL tables)

Knowledge lives in **PostgreSQL** (Docker service `db`, database **`kb`**), not in files or the repo. **`POST /documents`** and the UI write rows the backend reads for search and ask.

| Table | What it holds |
| --- | --- |
| **`documents`** | One row per article: `id`, `title`, `content`, `created_at` |
| **`chunks`** | Split text + **pgvector** embedding: `document_id`, `chunk_index`, `text`, `embedding` |
| **`questions`** | Ask history: `question`, `answer`, `source_chunk_ids`, **`latency_ms`**, `created_at` |

**`latency_ms`** on **`questions`** is end-to-end server time for that **`POST /ask`** in **milliseconds** (e.g. `9` = 9 ms, `1200` ≈ 1.2 s), including embed, retrieval, and LLM when used.

Tables are created when the **backend** starts. Vector search uses an HNSW index on `chunks.embedding`.

### View tables in pgAdmin (included in Docker)

1. Start the stack: `.\docker-up.ps1` or `docker compose up -d --build`.
2. Open **http://localhost:5050** and sign in:
   - Email: `admin@local.dev`
   - Password: `admin` (override with `PGADMIN_DEFAULT_*` in `.env`)
3. **Register → Server…** (browser pgAdmin **inside** Docker):
   - **General → Name:** `Mini KB`
   - **Connection → Host:** `db` (Docker network name — **not** `localhost`)
   - **Port:** `5432` (inside the container)
   - **Database / user / password:** `kb` / `kb` / `kb`
4. Expand **Servers → Mini KB → Databases → kb → Schemas → public → Tables** (`documents`, `chunks`, `questions`).

### pgAdmin desktop (installed on Windows)

Use **Host** `localhost` (or `127.0.0.1`) and **Port** **`5433`** — Docker maps Postgres to **5433** by default so it does not clash with a local PostgreSQL on **5432**. Same user/password/database: `kb` / `kb` / `kb`.

### CLI (optional)

```powershell
docker compose exec -it db psql -U kb -d kb -c "\dt public.*"
```

## Troubleshooting

| Problem | What to do |
| --- | --- |
| pgAdmin: **failed to resolve host `db`** | You are using **desktop** pgAdmin on Windows — use host **`localhost`**, port **`5433`**, not `db`. Use host **`db`** only in browser pgAdmin at localhost:5050. |
| pgAdmin: **password authentication failed for user kb** on port 5432 | You are hitting **Windows PostgreSQL**, not Docker — connect on port **`5433`**. |
| “Couldn’t find in knowledge base” | Run `POST /documents/reindex` after switching embedding model; re-add docs if DB was reset |
| “Gemini model not found or retired” | Set `LLM_MODEL=gemini-3.5-flash-lite`, then `docker compose up -d --force-recreate backend` |
| UI “service unavailable” on Ask | Check `docker compose logs backend`; ensure BGE is in Docker image or use reindex |
| CORS errors | Add your UI origin to `CORS_ORIGINS` |
| Rate limit 429 | Wait for `Retry-After` or raise `RATE_LIMIT_PER_MINUTE` locally |

## Tests

```powershell
cd backend
pip install -e ".[dev]"
pytest -q
```

Requires Postgres running (`docker compose up -d db`). For host tests, point `DATABASE_URL` at `localhost:5433` if using Docker db.

## Project layout

```
backend/app/          FastAPI, RAG, providers
frontend/src/         React UI
docker-compose.yml    db, pgadmin, backend, frontend
.env.example          template (no secrets)
ARCHITECTURE.md       design and scale notes
AI_USAGE.md           AI disclosure
```

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — data model, RAG flow, 10K / 100K / 1M scale
- [AI_USAGE.md](./AI_USAGE.md) — AI tools disclosure

## License

For evaluation purposes.
