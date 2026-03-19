# COLD Archive: db-schema-embeddings / S001
> Archived: 2026-03-18 | Status: DONE | Sign-off: ALL APPROVED

---

## Story Summary
S001: Create core database schema
- Migration: `001_create_core_schema.sql` — 4 tables (user_groups, documents, embeddings, audit_logs)
- ORM models: UserGroup, Document, Embedding, AuditLog (SQLAlchemy 2.0 Mapped[] style)
- Package: `backend/db/models/__init__.py` — re-exports all models + Base
- Tests: `tests/db/test_models.py` — 14 tests, 100% pass (SQLite in-memory)

## Key Decisions (S001 scope)
| ID  | Decision | Rationale |
|-----|----------|-----------|
| D05 | UserGroup.id uses Identity() | SQL standard GENERATED ALWAYS AS IDENTITY (not legacy SERIAL) |
| D06 | TDD mandatory | Tests co-located in task TOUCH list, written first during /implement |
| D07 | .venv/ + requirements.txt pinned | Reproducible env, resolves Pylance warnings |

## Files Created (S001)
- backend/db/migrations/001_create_core_schema.sql
- backend/db/models/base.py
- backend/db/models/user_group.py
- backend/db/models/document.py
- backend/db/models/embedding.py (no Vector col — added S002)
- backend/db/models/audit_log.py
- backend/db/models/__init__.py
- tests/db/test_models.py (14 tests)
- tests/__init__.py
- tests/db/__init__.py
- requirements.txt
- pytest.ini
- .venv/ (Python 3.12.10)

## Reviews
- S001-T001: APPROVED (migration 001)
- S001-T002: APPROVED (4 ORM models, Identity() fix)
- S001-T002b: APPROVED (14 unit tests, unused import fix)
- S001-T003: APPROVED (models/__init__.py)

## Report
Path: docs/reports/db-schema-embeddings-S001.report.md
AC Coverage: 5/5 (100%) | Test pass rate: 14/14 (100%)
Sign-off: Tech Lead ✅ | Product Owner ✅ | QA Lead ✅ — 2026-03-18
