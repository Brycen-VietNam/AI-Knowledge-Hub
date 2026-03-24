# Code Review: S001 — Users table + API-key schema migration (Story-level)
Feature: auth-api-key-oidc | Level: full | Date: 2026-03-23 | Reviewer: Claude (opus)

---

## Files Reviewed (8)

| File | Task | Action |
|------|------|--------|
| `backend/db/migrations/004_create_users_api_keys.sql` | T001 | created |
| `backend/db/models/user.py` | T002 | created |
| `backend/db/models/api_key.py` | T003 | created |
| `backend/db/models/audit_log.py` | T004 | modified |
| `backend/db/models/__init__.py` | T004 | modified |
| `tests/db/test_auth_models.py` | T005 | created |
| `tests/db/test_models.py` | T005 | modified |

## Schema ↔ ORM Consistency

| Column | Migration DDL | ORM Model | Match |
|--------|--------------|-----------|-------|
| `users.id` | `UUID PK DEFAULT gen_random_uuid()` | `Mapped[uuid.UUID] default=uuid.uuid4` | ✅ |
| `users.sub` | `TEXT NOT NULL UNIQUE` | `Mapped[str] unique=True, nullable=False` | ✅ |
| `users.email` | `TEXT` (nullable) | `Mapped[str \| None] nullable=True` | ✅ |
| `users.display_name` | `TEXT` (nullable) | `Mapped[str \| None] nullable=True` | ✅ |
| `users.is_active` | `BOOL NOT NULL DEFAULT TRUE` | `Mapped[bool] default=True, nullable=False` | ✅ |
| `users.created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | `Mapped[datetime] server_default=func.now()` | ✅ |
| `api_keys.user_id` | `UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE` | `Mapped[uuid.UUID] ForeignKey("users.id", ondelete="CASCADE")` | ✅ |
| `api_keys.key_hash` | `TEXT NOT NULL UNIQUE` | `Mapped[str] unique=True, nullable=False` | ✅ |
| `api_keys.user_group_ids` | `INTEGER[] NOT NULL DEFAULT '{}'` | `Mapped[list[int]] ARRAY(Integer) default=list` | ✅ |
| `api_keys.last_used_at` | `TIMESTAMPTZ` (nullable) | `Mapped[datetime \| None] nullable=True` | ✅ |
| `api_keys.created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | `Mapped[datetime] server_default=func.now()` | ✅ |
| `audit_logs.user_id` | `UUID` (altered) + `FK → users(id) NOT VALID` | `Mapped[uuid.UUID] ForeignKey("users.id")` | ✅ |

**12/12 columns match** — zero DDL/ORM drift.

## Full Checks

- [x] All individual task review_criteria satisfied
- [x] Test command passes — 21/21 passed
- [x] No files outside story scope modified
- [x] No magic numbers — defaults are spec-driven
- [x] No commented-out dead code (migration rollback is by convention)
- [x] S001: No string interpolation in SQL
- [x] R002: No PII in api_keys — `key_hash` only
- [x] A001: No cross-boundary imports
- [x] S005: No hardcoded secrets
- [x] A006: Migration numbered with rollback section
- [x] `__init__.py` exports 7 models consistently

## Cross-file Coherence

- [x] Migration DDL ↔ ORM models: 12/12 columns match exactly
- [x] `__init__.py` imports both new models
- [x] Tests cover User, ApiKey, AuditLog FK, uniqueness, exports
- [x] SQLite ARRAY caveat handled consistently in both test files

## Issues Found

### ⚠️ WARNING — Minor (non-blocking)

1. **Migration rollback L61**: `DROP INDEX IF EXISTS idx_users_sub` after `DROP TABLE IF EXISTS users CASCADE` — redundant (CASCADE drops index). Harmless, keeps rollback explicit.

2. **`test_models.py` L135**: `test_audit_log_user_id_is_uuid` inserts AuditLog with dangling `user_id` UUID (no User row). Works because SQLite FK enforcement is off by default. Proper FK chain tested in `test_auth_models.py:85`. Acceptable — test purpose is column type, not FK integrity.

3. **`test_auth_models.py` L9**: `from sqlalchemy import ... text` — unused import `text`.

## Verdict
**[x] APPROVED** [ ] CHANGES REQUIRED [ ] BLOCKED

Blockers: 0 | Warnings: 3 (minor) | Tests: 21/21 passed

## Task Status Summary

| Task | Status |
|------|--------|
| T001 | REVIEWED ✅ |
| T002 | REVIEWED ✅ |
| T003 | REVIEWED ✅ |
| T004 | REVIEWED ✅ |
| T005 | REVIEWED ✅ |

**Story S001 fully REVIEWED and APPROVED.**
