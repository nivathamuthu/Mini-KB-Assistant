# AI usage disclosure

I used AI coding tools during this challenge, as the brief encourages. I made the design decisions and reviewed, tested, and corrected the output myself.

## Tools and what I used them for

- **Cursor Agent (Claude):** first drafts of the repo scaffold, backend routes and services, React components, and tests.
- **Claude (chat):** reviewing my README and ARCHITECTURE.md against the brief and drafting the expanded scalability section, which I then edited.

## Decisions I made

- Chose the stack: FastAPI, PostgreSQL + pgvector, Gemini for answers, local BGE for embeddings, React/Vite.
- Chose to keep a mock mode so reviewers can run the app without API keys.
- [Add other decisions: chunk size, relevance threshold, rate limit approach, etc.]

## What I reviewed, tested, and changed

- Ran the full flow (add article, ask, view sources) in mock and Gemini mode.
- Ran the tests against a real Postgres + pgvector database.
- Checked that no secrets are in the repo or Git history and that errors don't leak internals.
- [Add real fixes or edits you made to AI-generated code.]

## Example of a suggestion I changed

**AI suggestion:** random hash-based vectors for mock embeddings.
**My decision:** changed it. Random hashes don't retrieve related chunks, which breaks the demo. I replaced them with normalized bag-of-words vectors so shared words raise cosine similarity. Mock mode is still labelled demo-only.

## Limits

- Gemini model IDs change over time, so I made `LLM_MODEL` configurable and kept mock mode as a fallback.
- [Add anything else you did not fully verify.]