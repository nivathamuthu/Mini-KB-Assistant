# Mini Knowledge Assistant

A small RAG (retrieval-augmented generation) service for an internal support team. Users add knowledge articles, ask questions in natural language, and get a grounded answer with source references.

- **Backend:** Python 3.11+, FastAPI (async), PostgreSQL + pgvector
- **Frontend:** React (Vite) + TypeScript
- **LLM / Embeddings:** pluggable provider (OpenAI-compatible) with a **mock fallback** (`PROVIDER=mock`)

## Requirements checklist

| Area | Requirement | Status |
| --- | --- | --- |
| API | `POST /documents`, `GET /documents`, `POST /ask` | ☑ |
| Validation | Reject empty / oversized input with 4xx and useful messages | ☑ |
| RAG | Chunking → embeddings → vector search → grounded generation → sources | ☑ |
| Fallback | Mock/local embeddings + LLM, clearly labelled as demo-only | ☑ |
| UI | Question box, Ask button, loading, answer, sources, error state | ☑ |
| Rate limit | `POST /ask` ≈ 20 req/min per client, HTTP 429 + `Retry-After` | ☑ |
| Errors | Timeouts, bounded retries, upstream 429 handling, no secret/stack leaks | ☑ |
| Tests | Focused tests for important API behaviour | ☑ |
| Docs | README, ARCHITECTURE.md, AI_USAGE.md | ☑ |

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Compose (PostgreSQL with pgvector)

## Setup and run

### All-in-Docker (recommended on Windows)

Start **Docker Desktop**, then from PowerShell in the repo root:

```powershell
.\docker-up.ps1
```

Or manually:

```powershell
docker compose up -d --build
```

- UI: http://localhost:5173  
- API: http://localhost:8001 (default; avoids clash if port 8000 is already in use)

To use different host ports: `$env:API_HOST_PORT="8002"; $env:UI_HOST_PORT="5174"; docker compose up -d --build`

Stop: `docker compose down`

### Local development (Python + Node on the host)

```bash
# 1. Postgres (pgvector)
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy ..\.env.example ..\.env    # Windows (or cp on Unix)
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health (includes `"mode": "mock"` when using mock providers)

### Tests

```bash
cd backend
pytest -q
```

## Configuration

Copy `.env.example` to `.env` at the repo root. Key variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://kb:kb@localhost:5432/kb` | Async Postgres URL |
| `PROVIDER` | `mock` | `mock`, `openai`, or `gemini` |
| `GEMINI_API_KEY` | — | Required when `PROVIDER=gemini` (set only in `.env`, never commit) |
| `EMBEDDING_DIM` | `384` (mock) / `768` (Gemini) / `1536` (OpenAI) | Must match vector column; reset DB when changing |
| `RATE_LIMIT_PER_MINUTE` | `20` | Per-client limit on `POST /ask` |

See `.env.example` for the full list.

### Google Gemini + local embeddings (recommended)

1. Copy `.env.example` → `.env` and set (never commit `.env`):
   ```env
   LLM_PROVIDER=google
   GOOGLE_API_KEY=your_key_from_google_ai_studio
   LLM_MODEL=gemini-2.0-flash
   EMBED_MODEL=BAAI/bge-small-en-v1.5
   EMBEDDING_DIM=384
   ```
2. Install local embedding runtime on the host: `pip install -e ".[local]"` in `backend/`.
3. Reset DB if vector size changed: `docker compose down -v` then `docker compose up -d --build`.
4. Re-add articles; `/health` should show `"mode": "google"`.

`GEMINI_API_KEY` and legacy `PROVIDER=gemini` still work. Docker loads optional `.env` for the backend.

## API quick reference

```bash
curl -X POST localhost:8000/documents -H "Content-Type: application/json" ^
  -d "{\"title\":\"Refund Policy\",\"content\":\"Customers may request a refund within 30 days.\"}"

curl "localhost:8000/documents?limit=10&offset=0"

curl -X POST localhost:8000/ask -H "Content-Type: application/json" ^
  -d "{\"question\":\"How long do I have to request a refund?\"}"
```

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — design, failure behaviour, scalability (10K / 100K / 1M)
- [AI_USAGE.md](./AI_USAGE.md) — AI tools disclosure

## License

For evaluation purposes.
