# Report: db-schema-embeddings / S001 — Create core database schema
Generated: 2026-03-18 | Agent: db-agent | Status: ✅ COMPLETE

---

## Executive Summary

| Field | Value |
|-------|-------|
| Story | S001: Create core database schema |
| Feature | db-schema-embeddings (P0) |
| Status | COMPLETE — all tasks REVIEWED |
| Duration | 1 session (2026-03-18) |
| Tasks | 4 (T001, T002, T002b, T003) — all REVIEWED ✅ |
| Test pass rate | 14/14 (100%) |
| AC coverage | 5/5 (100%) |
| Blockers resolved | 1 (D05: Identity() fix) |
| Blockers deferred | 0 |

---

## Changes Summary

### Database
| File | Action | Description |
|------|--------|-------------|
| `backend/db/migrations/001_create_core_schema.sql` | CREATE | 4 tables: user_groups, documents, embeddings, audit_logs. Rollback section included. |

### Code
| File | Action | Description |
|------|--------|-------------|
| `backend/db/models/base.py` | CREATE | `DeclarativeBase` shared by all ORM models |
| `backend/db/models/user_group.py` | CREATE | `UserGroup` model — INT IDENTITY PK |
| `backend/db/models/document.py` | CREATE | `Document` model — UUID PK, lang CHAR(2), user_group_id FK |
| `backend/db/models/embedding.py` | CREATE | `Embedding` model — no Vector column yet (S002) |
| `backend/db/models/audit_log.py` | CREATE | `AuditLog` model — user_id TEXT placeholder |
| `backend/db/models/__init__.py` | CREATE | Re-exports Base + 4 models via `__all__` |

### Tests
| File | Action | Description |
|------|--------|-------------|
| `tests/db/test_models.py` | CREATE | 14 pytest tests (SQLite in-memory, no live DB) |
| `tests/__init__.py` | CREATE | Package marker |
| `tests/db/__init__.py` | CREATE | Package marker |

### Config
| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | CREATE | Pinned: sqlalchemy=2.0.48, asyncpg=0.29.0, pgvector=0.3.6, pytest=8.3.5, pytest-asyncio=0.25.3 |
| `pytest.ini` | CREATE | `asyncio_mode=auto`, `asyncio_default_fixture_loop_scope=function` |
| `.venv/` | CREATE | Python 3.12.10 virtual environment |

---

## Test Results

### Unit Tests — `pytest tests/db/test_models.py -v`
**Result: 14/14 PASSED ✅**

| Test | Category | Result |
|------|----------|--------|
| test_user_group_tablename | Table name | ✅ |
| test_document_tablename | Table name | ✅ |
| test_embedding_tablename | Table name | ✅ |
| test_audit_log_tablename | Table name | ✅ |
| test_embeddings_has_no_vector_column | Column absence | ✅ |
| test_documents_has_no_content_fts_column | Column absence | ✅ |
| test_embeddings_has_user_group_id | Column presence (RBAC) | ✅ |
| test_document_fk_to_user_groups | FK relationship | ✅ |
| test_embedding_fk_to_documents | FK relationship | ✅ |
| test_audit_log_fk_to_documents | FK relationship | ✅ |
| test_user_group_insert | Roundtrip insert | ✅ |
| test_document_insert | Roundtrip insert | ✅ |
| test_audit_log_user_id_is_text | Placeholder constraint | ✅ |
| test_models_init_exports | Package export (T003) | ✅ |

### Integration Tests
N/A — no live PostgreSQL required at this stage. Migration SQL verified by review.

---

## Code Review Results

| Task | Level | Verdict | Issues |
|------|-------|---------|--------|
| T001 — migration 001 | quick | APPROVED ✅ | WARN: audit_logs ON DELETE RESTRICT intentional (preserves audit trail) |
| T002 — 4 ORM models | quick | APPROVED ✅ | WARN-02: autoincrement→Identity() fixed inline (D05) |
| T002b — unit tests | quick | APPROVED ✅ | WARN: unused `text` import removed |
| T003 — models/__init__.py | quick | APPROVED ✅ | None |

---

## Acceptance Criteria Coverage

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | `user_groups(id INT IDENTITY, name, created_at)` exists | ✅ PASS | migration 001 L1-5; UserGroup model; test_user_group_tablename |
| AC2 | `documents(id UUID, title, lang CHAR(2), user_group_id FK, created_at, updated_at)` exists | ✅ PASS | migration 001 L7-16; Document model; test_document_fk_to_user_groups |
| AC3 | `embeddings` metadata = {doc_id, lang, user_group_id, created_at} only — no PII (C002) | ✅ PASS | Embedding model has no Vector column (S002), no PII fields; test_embeddings_has_user_group_id |
| AC4 | `audit_logs(id UUID, user_id TEXT, doc_id FK, query_hash, accessed_at)` exists (C008) | ✅ PASS | migration 001 L24-33; AuditLog model; test_audit_log_user_id_is_text |
| AC5 | Migration `001_create_core_schema.sql` with rollback section (C010) | ✅ PASS | File created with `-- ROLLBACK` section; DROP TABLE CASCADE in reverse order |

**AC Coverage: 5/5 (100%)**

---

## Key Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| D05 | `UserGroup.id` uses `Identity()` not `autoincrement=True` | Maps to SQL standard `GENERATED ALWAYS AS IDENTITY`; `autoincrement=True` → legacy `SERIAL` |
| D06 | TDD mandatory: test written in same task, test first | Prevents missing coverage; adopted from T003 onwards; updated `.claude/commands/tasks.md` |
| D07 | `.venv/` at repo root, `requirements.txt` pinned | Reproducible environment; resolves Pylance import warnings |

---

## Blockers & Deferred Items

### Resolved
| ID | Blocker | Resolution |
|----|---------|------------|
| — | `autoincrement=True` maps to legacy SERIAL | Fixed: `Identity()` in UserGroup model (D05) |
| — | Missing unit tests for T002 | Added T002b as explicit task; adopted TDD convention (D06) |
| — | Pylance `Import "sqlalchemy" could not be resolved` | Created `.venv/` + `requirements.txt` (D07) |

### Deferred to S002+
| Item | Reason | Story |
|------|--------|-------|
| `embedding` Vector(1024) column | Requires pgvector extension (migration 002) | S002/T002 |
| `content_fts` tsvector column | CJK FTS migration | S003/T002 |
| `audit_logs.user_id` FK to users | Auth schema TBD | auth-agent |

---

## Rollback Plan

```sql
-- Run in order to tear down S001 schema
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS embeddings CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS user_groups CASCADE;
```

- **Downtime**: None at schema creation. Rollback requires app restart.
- **Data loss risk**: HIGH — drops all data in 4 tables. Only safe before data ingestion starts.
- **Procedure**: Run rollback SQL → redeploy without migration → confirm `\dt` shows no tables.

---

## Lessons Learned

### What went well
- SQLite in-memory engine for unit tests: fast, no infrastructure dependency
- `tests/` outside `backend/` aligns with Python project convention + Docker safety
- `/reviewcode` after each `/implement` caught issues early (Identity(), unused import)

### Improvements adopted
- TDD convention (`D06`) added to `.claude/commands/tasks.md` — applies to all future `/tasks` runs
- `requirements.txt` + `.venv/` from session start — prevents mid-session interpreter issues

### Rule additions
- None — all existing CONSTITUTION/HARD rules satisfied

---

## Sign-Off

- [ ] Tech Lead: _pending_
- [ ] Product Owner: _pending_
- [ ] QA Lead: _pending_

After all approvals, run:
```
/report db-schema-embeddings/S001 --finalize
```
→ Archives WARM → COLD
→ Updates HOT.md
→ Unblocks S002 start
