# Mini Knowledge Assistant

A small RAG (retrieval-augmented generation) service for an internal support team. Users add knowledge articles, ask questions in natural language, and get a grounded answer with source references.

- **Backend:** Python 3.11+, FastAPI (async), PostgreSQL + pgvector
- **Frontend:** React (Vite) + TypeScript
- **Embeddings:** local **BGE** (`EMBED_MODEL`) in Docker/local, or mock / OpenAI / Gemini API
- **LLM:** **Google Gemini** (`LLM_PROVIDER=google`), OpenAI, or **mock** demo mode

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

- **Docker Desktop** (recommended: runs db + backend + frontend)
- Or: Python 3.11+, Node 18+, Docker only for Postgres

## Quick start (Docker — recommended)

1. Copy env file and add your Google key (never commit `.env`):

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
# 1. Database only
docker compose up -d db

# 2. Backend
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

### Recommended production-style local setup

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=your_key_from_google_ai_studio
LLM_MODEL=gemini-3.5-flash-lite
EMBED_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384
```

| Variable | Description |
| --- | --- |
| `LLM_PROVIDER` | `google`, `openai`, or `mock` |
| `GOOGLE_API_KEY` | Gemini API key (`GEMINI_API_KEY` also works) |
| `LLM_MODEL` | Chat model, e.g. `gemini-3.5-flash-lite` or `gemini-3.8-flash` |
| `EMBED_MODEL` | Local Hugging Face model for search (e.g. BGE); Docker image includes it |
| `EMBEDDING_DIM` | `384` for BGE-small; `768` for Gemini API embeddings; `1536` for OpenAI |
| `TOP_K` / `MIN_RELEVANCE_SCORE` | Retrieval tuning (default 4 / 0.15) |

Legacy: `PROVIDER=mock|openai|gemini` still works. Retired Gemini 2.x model names are auto-mapped to 3.x in config.

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
| `GET` | `/documents` | List titles (paginated) |
| `POST` | `/documents/reindex` | Re-embed all documents (after changing `EMBED_MODEL`) |
| `POST` | `/ask` | RAG question → answer + sources |
| `GET` | `/health` | `status`, `mode` (`google`, `mock`, etc.) |

### Examples (Docker API on port 8001)

```powershell
curl -X POST http://localhost:8001/documents -H "Content-Type: application/json" -d "{\"title\":\"Refund Policy\",\"content\":\"Customers may request a refund within 30 days.\"}"

curl "http://localhost:8001/documents?limit=10&offset=0"

curl -X POST http://localhost:8001/ask -H "Content-Type: application/json" -d "{\"question\":\"Explain the Refund Policy?\"}"

curl -X POST http://localhost:8001/documents/reindex
```

## Data storage (PostgreSQL tables)

Knowledge is **not** kept in the repo, `.env`, or comment blocks. When you use **Add document** or `POST /documents`, the backend writes rows into a real **PostgreSQL** database (Docker service `db`, database name `kb`).

| Table | What it holds |
| --- | --- |
| **`documents`** | One row per article: `id`, `title`, `content`, `created_at` |
| **`chunks`** | Split text + **pgvector** embedding per piece: `document_id`, `chunk_index`, `text`, `embedding` |
| **`questions`** | Ask history: question, answer, source chunk ids, latency |

Tables are created when the **backend** starts (`CREATE EXTENSION vector` + SQLAlchemy `create_all`). Start the full stack once before expecting tables in pgAdmin. Vector search uses an HNSW index on `chunks.embedding`.

### View tables in pgAdmin (included in Docker)

1. Start the stack: `.\docker-up.ps1` or `docker compose up -d --build`.
2. Open **http://localhost:5050** and sign in:
   - Email: `admin@local.dev`
   - Password: `admin` (override with `PGADMIN_DEFAULT_*` in `.env`)
3. **Register → Server…**
   - **General → Name:** `Mini KB` (any label)
   - **Connection → Host name:** `db` (Docker service name, not `localhost`)
   - **Port:** `5432`
   - **Maintenance database:** `kb`
   - **Username / Password:** `kb` / `kb`
   - Save (no SSL for local dev)
4. In the tree, expand:

   **Servers → Mini KB → Databases → kb → Schemas → public → Tables**

   You should see **`documents`**, **`chunks`**, and **`questions`**. Right‑click a table → **View/Edit Data → All Rows** to browse rows.

### pgAdmin desktop (installed on Windows)

Use the same credentials, but set **Host** to **`localhost`** (port `5432`), because pgAdmin runs outside Docker.

### CLI (optional)

```powershell
docker compose exec -it db psql -U kb -d kb -c "\dt public.*"
```

## Troubleshooting

| Problem | What to do |
| --- | --- |
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

Requires Postgres running (`docker compose up -d db`).

## Project layout

```
backend/app/          FastAPI, RAG, providers
frontend/src/         React UI
docker-compose.yml    db + backend + frontend
.env.example          template (no secrets)
ARCHITECTURE.md       design and scale notes
AI_USAGE.md           AI disclosure
```

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — data model, RAG flow, 10K / 100K / 1M scale
- [AI_USAGE.md](./AI_USAGE.md) — AI tools disclosure

## License

For evaluation purposes.
