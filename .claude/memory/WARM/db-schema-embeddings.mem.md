# Feature Memory: db-schema-embeddings
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: DONE ✅ — all 4 stories complete & archived to COLD
Updated: 2026-03-19

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
Task files: `docs/tasks/db-schema-embeddings/S001-S004.tasks.md`

| Story | Task File | Tasks | Status |
|-------|-----------|-------|--------|
| S001 | S001.tasks.md | T001 ✅ T002 ✅ T002b ✅ T003 ✅ | DONE — archived COLD |
| S002 | S002.tasks.md | T001 ✅ T002 ✅ | DONE — archived COLD |
| S003 | S003.tasks.md | T001 ✅ T002 ✅ | DONE — archived COLD |
| S004 | S004.tasks.md | T001 ✅ T002 ✅ | DONE — archived COLD |

Total atomic tasks: 10 (T002b added)

Task detail:
- T001 migration 001_create_core_schema.sql — REVIEWED ✅
- T002 4 ORM models (UserGroup/Document/Embedding/AuditLog) — REVIEWED ✅
- T002b unit tests tests/db/test_models.py (13 tests) — REVIEWED ✅
- T003 models/__init__.py — REVIEWED ✅

## Files Touched
backend/db/migrations/001_create_core_schema.sql (created)
backend/db/models/base.py (created)
backend/db/models/user_group.py (created — Identity() fix applied)
backend/db/models/document.py (created)
backend/db/models/embedding.py (created — no Vector col yet, S002)
backend/db/models/audit_log.py (created)
tests/db/test_models.py (created — 13 tests, all pass)
tests/__init__.py (created)
tests/db/__init__.py (created)
docs/reviews/S001-T001.review.md (created — APPROVED)
docs/reviews/S001-T002.review.md (created — APPROVED)
docs/reviews/S001-T002b.review.md (created — APPROVED)

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

---

## Sync: 2026-03-18 (/tasks)
Decisions added: none
Tasks changed: WARM task board updated — 9 atomic tasks across 4 stories
Files touched (this session):
  docs/tasks/db-schema-embeddings/S001.tasks.md (created — 3 tasks)
  docs/tasks/db-schema-embeddings/S002.tasks.md (created — 2 tasks)
  docs/tasks/db-schema-embeddings/S003.tasks.md (created — 2 tasks)
  docs/tasks/db-schema-embeddings/S004.tasks.md (created — 2 tasks)
Questions resolved: none
New blockers: none

---

## Sync: 2026-03-18 (/implement S001 T001–T002b)
Decisions added: D05 — UserGroup.id uses Identity() not autoincrement (SQL standard, aligns with GENERATED ALWAYS AS IDENTITY in migration 001)
Tasks changed: T001→REVIEWED, T002→REVIEWED, T002b→REVIEWED (new task added), T003→TODO
Files touched: see ## Files Touched section
Questions resolved: none
New blockers: none
Note: tests/ placed outside backend/ — Python convention, Docker-safe

---

## Sync: 2026-03-18 (session #004 — conventions + venv)
Decisions added:
  D06 — TDD mandatory: test in same task TOUCH list, /implement writes test first then code
  D07 — venv at .venv/; requirements.txt pinned: sqlalchemy=2.0.48, asyncpg=0.29.0, pgvector=0.3.6, pytest=8.3.5, pytest-asyncio=0.25.3
Tasks changed: none (T003 still TODO)
Files touched:
  .venv/ (created — Python 3.12.10)
  requirements.txt (created)
  pytest.ini (created — asyncio_mode=auto, loop_scope=function)
  .claude/commands/tasks.md (TDD convention added — mandatory from T003 onwards)
  docs/tasks/db-schema-embeddings/S002.tasks.md (T002 updated — test co-located)
  docs/tasks/db-schema-embeddings/S003.tasks.md (T002 updated — test co-located)
  docs/tasks/db-schema-embeddings/S004.tasks.md (T001+T002 updated — test co-located)
Questions resolved: none
New blockers: none
Note: VSCode must use .venv interpreter (Ctrl+Shift+P → Python: Select Interpreter → .venv\Scripts\python.exe)
