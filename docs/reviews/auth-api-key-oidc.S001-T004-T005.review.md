# Code Review: S001-T004 + T005 — AuditLog FK update + Tests
Feature: auth-api-key-oidc | Level: full | Date: 2026-03-23 | Reviewer: Claude (opus)

---

## T004: Update AuditLog ORM (TEXT→UUID FK) + models __init__

### Task Review Criteria
- [x] `audit_log.py`: `user_id: Mapped[uuid.UUID]` with `ForeignKey("users.id")` — L16
- [x] `audit_log.py`: old TEXT placeholder comment removed
- [x] `__init__.py`: exports `User` and `ApiKey` alongside existing 5 exports — L7-8
- [x] `__all__` has 7 entries: `Base, UserGroup, Document, Embedding, AuditLog, User, ApiKey` — L10
- [x] No other logic changed in audit_log.py

### Full Checks
- [x] No files outside TOUCH list modified
- [x] No magic numbers
- [x] No commented-out dead code
- [x] Pattern consistent with existing models

---

## T005: Tests — test_auth_models.py + fix test_models.py

### Task Review Criteria
- [x] `test_user_tablename` — asserts `User.__tablename__ == "users"`
- [x] `test_api_key_tablename` — asserts `ApiKey.__tablename__ == "api_keys"`
- [x] `test_user_sub_unique(session)` — insert two users with same `sub` → `IntegrityError`
- [x] `test_api_key_no_plaintext` — `"key_plaintext"` NOT in column names (ORM class inspection)
- [x] `test_audit_log_fk_to_users(engine)` — FK target `("users", ["id"])` in inspect
- [x] `test_audit_log_user_id_is_uuid(session)` — full User→AuditLog chain, asserts `isinstance(log.user_id, uuid.UUID)`
- [x] `test_models_init_exports_auth` — `from backend.db.models import User, ApiKey` both work
- [x] `test_models.py::test_audit_log_user_id_is_text` renamed + updated to use `uuid.uuid4()`
- [x] All existing `test_models.py` tests still pass — **21/21 passed**
- [x] TDD: tests cover all new ORM columns and constraints

### Full Checks
- [x] No files outside TOUCH list modified
- [x] SQLite ARRAY caveat handled correctly — `api_keys` table excluded from `Base.metadata.create_all()` in both fixtures
- [x] `test_api_key_no_plaintext` uses ORM class inspection (not DB DDL) — correct for SQLite limitation
- [x] No magic numbers

### Observation (not a blocker)
`test_models.py::test_audit_log_user_id_is_uuid` inserts AuditLog with a dangling user_id UUID (no User row). Works because SQLite FK enforcement is off by default. Full FK chain is properly tested in `test_auth_models.py::test_audit_log_user_id_is_uuid`.

---

## Rules
- [x] A001: No cross-boundary imports in any modified file
- [x] R002: No PII columns
- [x] S001: No SQL string interpolation

## Issues Found
None.

## Verdict
**[x] APPROVED** [ ] CHANGES REQUIRED [ ] BLOCKED

Blockers: 0 | Test result: 21/21 passed
