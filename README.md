# Mini Knowledge Assistant

A small RAG (retrieval-augmented generation) service for an internal support team. Users add knowledge articles, ask questions in natural language, and get a grounded answer with source references.

- **Backend:** Python 3.11+, FastAPI (async), PostgreSQL + pgvector
- **Frontend:** React (Vite) + TypeScript
- **Embeddings:** local **BGE** (`EMBED_MODEL`) in Docker/local, or mock / OpenAI / Gemini API
- **LLM:** **Google Gemini** via `LLM_PROVIDER=google` and `GOOGLE_API_KEY` (same as Gemini API key), OpenAI, or **mock** demo mode

## Requirements checklist

Each row links to where the behaviour is implemented or tested.

| Area | Requirement | Evidence |
| --- | --- | --- |
| API | `POST /documents`, `GET /documents`, `POST /ask` | [`backend/app/api/documents.py`](backend/app/api/documents.py), [`backend/app/api/ask.py`](backend/app/api/ask.py); [`backend/tests/test_documents.py`](backend/tests/test_documents.py), [`backend/tests/test_ask.py`](backend/tests/test_ask.py) |
| Validation | Reject empty / oversized input with 4xx | [`backend/app/schemas.py`](backend/app/schemas.py); [`backend/tests/test_documents.py`](backend/tests/test_documents.py) (422) |
| RAG | Chunk → embed → search → generate → sources | [`backend/app/services/rag.py`](backend/app/services/rag.py), [`backend/app/services/retrieval.py`](backend/app/services/retrieval.py), [`backend/app/services/chunking.py`](backend/app/services/chunking.py) |
| Fallback | Mock embeddings + LLM (demo-only) | [`backend/app/services/embeddings.py`](backend/app/services/embeddings.py), [`backend/app/services/llm.py`](backend/app/services/llm.py); `/health` [`mode`](backend/app/api/health.py) |
| UI | Ask, loading, answer, sources, errors | [`frontend/src/App.tsx`](frontend/src/App.tsx), [`AskForm.tsx`](frontend/src/components/AskForm.tsx), [`SourceList.tsx`](frontend/src/components/SourceList.tsx), [`ErrorBanner.tsx`](frontend/src/components/ErrorBanner.tsx) |
| Rate limit | `POST /ask` ≈ 20/min, 429 + `Retry-After` | [`backend/app/rate_limit.py`](backend/app/rate_limit.py); [`backend/tests/test_rate_limit.py`](backend/tests/test_rate_limit.py) |
| Errors | Timeouts, retries, no secret leaks | [`backend/app/errors.py`](backend/app/errors.py), [`backend/app/main.py`](backend/app/main.py); upstream retry in [`backend/app/services/embeddings.py`](backend/app/services/embeddings.py), [`backend/app/services/llm.py`](backend/app/services/llm.py) |
| Tests | Focused API behaviour | [`backend/tests/`](backend/tests/) |
| Docs | README, architecture, AI disclosure | [README.md](./README.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [AI_USAGE.md](./AI_USAGE.md) |

## Prerequisites

- **Docker** (recommended: db + pgadmin + backend + frontend)
- Or: Python 3.11+, Node 18+, Docker **only** for Postgres (pgvector)

## Quick start (Docker — recommended)

**No API key?** Use **mock mode** first so reviewers can run the full UI without Gemini:

```env
LLM_PROVIDER=mock
EMBEDDING_DIM=384
```

Copy that into `.env` (see step 1), start Docker, add a document, and ask a question — answers are demo/extractive, labelled via `/health` `mode: "mock"`.

**Gemini models:** Defaults in `.env.example` (`gemini-3.5-flash-lite`, etc.) match this repo’s config and alias map in [`backend/app/config.py`](backend/app/config.py). Google changes model IDs over time; if `POST /ask` fails with “model not found”, pick a current model in [Google AI Studio](https://aistudio.google.com/) and set `LLM_MODEL`, or switch to **mock** above. Retired 2.x names are remapped automatically when listed in config.

### 1. Environment file

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
copy .env.example .env
# Edit .env: GOOGLE_API_KEY=... or use LLM_PROVIDER=mock
```

</details>

<details>
<summary><strong>macOS / Linux (bash)</strong></summary>

```bash
cp .env.example .env
# Edit .env: GOOGLE_API_KEY=... or use LLM_PROVIDER=mock
```

</details>

### 2. Start the stack

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
.\docker-up.ps1
```

Or:

```powershell
docker compose up -d --build
```

</details>

<details>
<summary><strong>macOS / Linux (bash)</strong></summary>

```bash
docker compose up -d --build
```

(`docker-up.ps1` is a Windows helper only; same as `docker compose up -d --build`.)

</details>

### 3. Open

| Service | URL |
| --- | --- |
| **UI** | http://localhost:5173 |
| **API** | http://localhost:8001 |
| **Swagger** | http://localhost:8001/docs |
| **Health** | http://localhost:8001/health |
| **pgAdmin** | http://localhost:5050 |

Default API host port is **8001** (avoids clash with other apps on 8000).

### 4. Try it

Add a knowledge article in the UI → ask a question → review answer and sources.

**After changing `.env`**, recreate the backend:

<details>
<summary><strong>Windows / macOS / Linux</strong></summary>

```bash
docker compose up -d --force-recreate backend
```

</details>

Stop: `docker compose down`  
Reset DB: `docker compose down -v` (then re-add documents)

## Local development (Python + Node on host)

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
docker compose up -d db
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,local]"
copy ..\.env.example ..\.env
uvicorn app.main:app --reload --port 8000
# New terminal:
cd frontend
npm install
npm run dev
```

</details>

<details>
<summary><strong>macOS / Linux (bash)</strong></summary>

```bash
docker compose up -d db
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,local]"
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000
# New terminal:
cd frontend
npm install
npm run dev
```

</details>

- API: http://localhost:8000  
- UI: http://localhost:5173 (set `VITE_API_URL=http://localhost:8000` if needed)  
- Host → Docker Postgres: `DATABASE_URL=...@localhost:5433/kb` (see `.env.example`)

## Configuration

Copy `.env.example` → `.env` at the repo root. **Never commit `.env`**.

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
| `LLM_MODEL` | Chat model ID for Gemini (verify in AI Studio if asks fail) |
| `EMBED_MODEL` | Local Hugging Face model for **search**; Docker image includes BGE |
| `EMBEDDING_DIM` | `384` (BGE-small), `768` (Gemini API embeddings), `1536` (OpenAI) |
| `DB_HOST_PORT` | Host port for Postgres (default **5433**) |
| `TOP_K` / `MIN_RELEVANCE_SCORE` | Retrieval tuning (default **4** / **0.15**) |
| `RATE_LIMIT_PER_MINUTE` | Max `POST /ask` requests per client per minute (default **20**) |
| `UPSTREAM_TIMEOUT_SECONDS` | Timeout for OpenAI/Gemini HTTP calls (default **20**) |
| `UPSTREAM_MAX_RETRIES` | Retries on timeout/5xx with backoff (default **2**) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Ingest splitting (default **800** / **120**) |
| `MAX_DOC_CHARS` / `MAX_TITLE_CHARS` / `MAX_QUESTION_CHARS` | Input caps (default **200000** / **200** / **1000**) |
| `CORS_ORIGINS` | Allowed browser origins for the UI |

Legacy: `PROVIDER=mock|openai|gemini` still works. Retired Gemini 2.x model IDs are auto-mapped in [`backend/app/config.py`](backend/app/config.py).

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

| Param | Default | Meaning |
| --- | --- | --- |
| `limit` | `20` | Max rows (1–100) |
| `offset` | `0` | Rows to skip (newest first) |

### `GET /health` — `status` and `mode`

- **`status: "ok"`** — API is running (does not call Gemini).
- **`mode`** — configuration only: `google`, `mock`, `openai`, `gemini`, `local`, etc.

### `POST /documents/reindex`

Rebuilds **`chunks`** for all **`documents`** after embedding or chunk setting changes. Restart backend after `.env` changes, then call once. No body.

### curl examples (Docker API on port 8001)

<details>
<summary><strong>macOS / Linux (bash)</strong></summary>

```bash
curl -X POST http://localhost:8001/documents \
  -H 'Content-Type: application/json' \
  -d '{"title":"Refund Policy","content":"Customers may request a refund within 30 days."}'

curl 'http://localhost:8001/documents?limit=10&offset=0'

curl -X POST http://localhost:8001/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Explain the Refund Policy?"}'

curl -X POST http://localhost:8001/documents/reindex

curl http://localhost:8001/health
```

</details>

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
curl -X POST http://localhost:8001/documents -H "Content-Type: application/json" -d "{\"title\":\"Refund Policy\",\"content\":\"Customers may request a refund within 30 days.\"}"

curl "http://localhost:8001/documents?limit=10&offset=0"

curl -X POST http://localhost:8001/ask -H "Content-Type: application/json" -d "{\"question\":\"Explain the Refund Policy?\"}"

curl -X POST http://localhost:8001/documents/reindex

curl http://localhost:8001/health
```

</details>

## Data storage (PostgreSQL tables)

Knowledge lives in **PostgreSQL** (Docker service `db`, database **`kb`**).

| Table | What it holds |
| --- | --- |
| **`documents`** | `id`, `title`, `content`, `created_at` |
| **`chunks`** | `document_id`, `chunk_index`, `text`, `embedding` (pgvector) |
| **`questions`** | Ask history: `question`, `answer`, `source_chunk_ids`, **`latency_ms`** (ms), `created_at` |

Tables are created when the **backend** starts.

### View tables in pgAdmin (included in Docker)

1. Start the stack (`docker compose up -d --build` or `.\docker-up.ps1` on Windows).
2. Open **http://localhost:5050** and sign in with **`admin@local.dev`** / **`admin`**.
   - **Local development only** — default pgAdmin credentials are not for production. Override with `PGADMIN_DEFAULT_*` in `.env` or do not expose port 5050 publicly.
3. **Register → Server…** (browser pgAdmin in Docker):
   - **Host:** `db` (not `localhost`)
   - **Port:** `5432` (inside the Docker network)
   - **Database / user / password:** `kb` / `kb` / `kb`
4. **Schemas → public → Tables** → `documents`, `chunks`, `questions`.

### pgAdmin desktop (on your machine)

**Host** `localhost`, **port** **`5433`** (Docker host mapping), user/password/database `kb`.

### CLI

```bash
docker compose exec -it db psql -U kb -d kb -c '\dt public.*'
```

## Troubleshooting

| Problem | What to do |
| --- | --- |
| pgAdmin: **failed to resolve host `db`** | Desktop pgAdmin: use **`localhost:5433`**. Browser pgAdmin (5050): use host **`db`**. |
| pgAdmin: **password failed for user kb** on 5432 | Wrong server — use Docker on port **`5433`**. |
| “Couldn’t find in knowledge base” | `POST /documents/reindex`; re-add docs if DB was reset |
| “Gemini model not found or retired” | Set a current model from AI Studio in `LLM_MODEL`, or use **`LLM_PROVIDER=mock`**; recreate backend |
| UI “service unavailable” on Ask | `docker compose logs backend`; check BGE / reindex |
| CORS errors | Add UI origin to `CORS_ORIGINS` |
| Rate limit 429 | Wait for `Retry-After` or raise **`RATE_LIMIT_PER_MINUTE`** in `.env` |

## Tests

**PostgreSQL with pgvector is required.** There is no SQLite or in-memory DB fallback — tests hit a real database via asyncpg (see [`backend/tests/conftest.py`](backend/tests/conftest.py)).

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
docker compose up -d db
cd backend
pip install -e ".[dev]"
pytest -q
```

</details>

<details>
<summary><strong>macOS / Linux (bash)</strong></summary>

```bash
docker compose up -d db
cd backend
pip install -e ".[dev]"
pytest -q
```

</details>

Default test URL: `postgresql+asyncpg://kb:kb@localhost:5433/kb` (Docker `db` with default `DB_HOST_PORT`). Override with `DATABASE_URL` if your port differs. Tests use **`PROVIDER=mock`** — no live Gemini/OpenAI calls.

If Docker is unavailable, you cannot run the integration tests as written; run the stack in Docker or install Postgres locally with the **pgvector** extension and match `DATABASE_URL`.

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

- [ARCHITECTURE.md](./ARCHITECTURE.md) — data model, RAG flow, scale notes
- [AI_USAGE.md](./AI_USAGE.md) — AI tools disclosure

## License

For evaluation purposes.
