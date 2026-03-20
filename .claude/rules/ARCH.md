# ARCHITECTURE RULES
# Checked by /plan and /analyze commands.

---

## A001 — Agent Scope Isolation
Each agent owns its directory. Cross-boundary calls via interfaces only.
- db-agent: never imports from backend/rag/ or backend/api/
- rag-agent: imports from backend/db/ only via repository interfaces
- api-agent: imports from backend/rag/ and backend/auth/ — never direct db access

## A002 — Dependency Direction
```
frontend → api → rag → db
              → auth
bots     → api (same as frontend)
```
No reverse dependencies. No circular imports.

## A003 — Language Detection
Auto-detect query language. Never hardcode `lang="en"` as fallback.
Use: langdetect or fasttext model at query entry point (backend/api/routes/query.py).
Response language = detected query language (unless user overrides).

## A004 — Hybrid Search Weight Contract
BM25 weight: 0.3 | Dense weight: 0.7 (default, configurable via env).
Must be parameterized — never hardcoded in business logic.
Config: `RAG_BM25_WEIGHT`, `RAG_DENSE_WEIGHT` environment variables.

## A005 — Error Response Shape
All API errors must follow:
```json
{"error": {"code": "ERR_CODE", "message": "...", "request_id": "..."}}
```
Never expose stack traces or internal paths in production responses.

## A006 — Migration Strategy
All schema changes via numbered migration files: `backend/db/migrations/NNN_description.sql`
Each migration must have a rollback section commented at bottom.
ORM models updated AFTER migration file is created and reviewed.
