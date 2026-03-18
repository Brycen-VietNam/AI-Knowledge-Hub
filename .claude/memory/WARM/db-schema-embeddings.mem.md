# Feature Memory: db-schema-embeddings
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: SPECCING
Updated: 2026-03-17

---

## Summary
- PostgreSQL schema: tables `user_groups`, `documents`, `embeddings`, `audit_logs`
- pgvector HNSW index (m=16, ef_construction=64, cosine) on `embeddings.embedding vector(1024)`
- Embedding model: multilingual-e5-large (1024 dims) — confirmed by stakeholder
- CJK FTS: `content_fts tsvector` column + GIN index; tokenization in application layer
- Connection pool: asyncpg, pool_size=10, max_overflow=10 (effective max=20)

## Key Decisions
| ID  | Decision | Rationale | Date |
|-----|----------|-----------|------|
| D01 | Embedding model: multilingual-e5-large (1024 dims) | Confirmed by stakeholder in /specify session | 2026-03-17 |
| D02 | CJK tokenization in app layer, not pg | PostgreSQL built-in parser doesn't support CJK properly | 2026-03-17 |
| D03 | asyncpg driver (postgresql+asyncpg://) | Assumed — confirm at /clarify | 2026-03-17 |

## Spec
Path: `docs/specs/db-schema-embeddings.spec.md`
Stories: 4 | Priority: P0

## Plan
Path: `docs/plans/db-schema-embeddings.plan.md`
Critical path: S001 → S002 → S003 → S004

## Task Progress
| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| T001 | S001 | TODO | db-agent | Core schema migration |
| T002 | S002 | TODO | db-agent | pgvector + HNSW index |
| T003 | S003 | TODO | db-agent | FTS column + GIN index |
| T004 | S004 | TODO | db-agent | session.py connection pool |

## Files Touched
_Updated by /sync after each implement session._

## Open Questions
| # | Question | Owner | Due |
|---|----------|-------|-----|
| Q1 | asyncpg driver confirmed? (assumption D03) | db-agent | /clarify |
| Q2 | pool_size split: pool_size=5 + max_overflow=15 vs pool_size=10 + max_overflow=10? | db-agent | /clarify |

## CONSTITUTION Violations Found
_None — spec aligns with C001–C014._
