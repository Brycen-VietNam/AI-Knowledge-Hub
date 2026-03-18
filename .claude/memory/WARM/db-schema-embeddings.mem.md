# Feature Memory: db-schema-embeddings
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: PLANNED
Updated: 2026-03-18

---

## Summary
- PostgreSQL schema: tables `user_groups`, `documents`, `embeddings`, `audit_logs`
- pgvector HNSW index (m=16, ef_construction=64, cosine) on `embeddings.embedding vector(1024)`
- Embedding model: multilingual-e5-large (1024 dims) — confirmed by stakeholder
- CJK FTS: `content_fts tsvector` column + GIN index; tokenization in application layer
- Connection pool: asyncpg, pool_size=5, max_overflow=15 (effective max=20)

## Key Decisions
| ID  | Decision | Rationale | Date |
|-----|----------|-----------|------|
| D01 | Embedding model: multilingual-e5-large (1024 dims) | Confirmed by stakeholder in /specify session | 2026-03-17 |
| D02 | CJK tokenization in app layer, not pg | PostgreSQL built-in parser doesn't support CJK properly | 2026-03-17 |
| D03 | asyncpg driver (postgresql+asyncpg://) | Confirmed by stakeholder 2026-03-18 | 2026-03-18 |
| D04 | pool_size=5, max_overflow=15 | 5 persistent + 15 burst = max 20. Confirmed 2026-03-18 | 2026-03-18 |

## Spec
Path: `docs/specs/db-schema-embeddings.spec.md`
Stories: 4 | Priority: P0

## Plan
Path: `docs/plans/db-schema-embeddings.plan.md`
Critical path: S001 → S002 → (S003 ∥ S004)
Groups: G1=S001→S002 sequential; G2=S003+S004 parallel after G1

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
_All resolved at /clarify 2026-03-18. See docs/clarify/db-schema-embeddings.clarify.md._

## CONSTITUTION Violations Found
_None — spec aligns with C001–C016 (CONSTITUTION v1.3)._

---

## Sync: 2026-03-18
Decisions added: D03 (asyncpg confirmed), D04 (pool_size=5/max_overflow=15)
Tasks changed: none (all TODO — /tasks not yet run)
Files touched (this session):
  docs/specs/db-schema-embeddings.spec.md (S003 tokenizer fix, S004 pool fix)
  docs/clarify/db-schema-embeddings.clarify.md (created)
  docs/reviews/db-schema-embeddings.checklist.md (created, PASS)
  docs/plans/db-schema-embeddings.plan.md (created)
  CONSTITUTION.md v1.2→v1.3 (C005 kiwipiepy, C015 LLM_PROVIDER, C016 Valkey, Tech Stack expanded)
  docs/backlog.md (restructured — 15 features, P0/P1/P2, dependency graph)
Questions resolved: Q1 (asyncpg), Q2 (pool split) — all /clarify BLOCKERs resolved
New blockers: none
