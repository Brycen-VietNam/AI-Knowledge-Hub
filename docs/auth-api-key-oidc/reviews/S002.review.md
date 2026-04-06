# Code Review: S002 — API-key authentication middleware (Story-level)
Feature: auth-api-key-oidc | Level: security | Date: 2026-03-23 | Reviewer: Claude (opus)

---

## Files Reviewed (5)

| File | Task | Action |
|------|------|--------|
| `backend/auth/__init__.py` | T001 | created (empty) |
| `backend/auth/_errors.py` | T001 | created |
| `backend/auth/api_key.py` | T002 | created |
| `tests/auth/__init__.py` | T003 | created (empty) |
| `tests/auth/test_api_key.py` | T003 | created |

## T001: auth package scaffold + _errors.py

### Task Review Criteria
- [x] `backend/auth/__init__.py` is an empty file — placeholder for S004
- [x] `_errors.py` defines `auth_error(request, code, message, status) -> HTTPException` — L12
- [x] `HTTPException.detail` shape: `{"error": {"code": ..., "message": ..., "request_id": ...}}` — L16-18
- [x] `request_id` fallback: `str(uuid.uuid4())` if not on `request.state` — L15
- [x] No imports from `backend/rag/` or `backend/api/` (A001)
- [x] Rule satisfied: A005 (error response shape)

## T002: verify_api_key implementation

### Task Review Criteria
- [x] `verify_api_key` signature: `async def verify_api_key(request: "Request", db: AsyncSession)` — L30
- [x] `X-API-Key` header missing or empty → raises `AUTH_MISSING` 401 — L32-34
- [x] Hash: `hashlib.sha256(key.encode()).hexdigest()` — L36
- [x] DB lookup: `select(ApiKey).join(User).where(ApiKey.key_hash == key_hash, User.is_active == True)` — L39-43
- [x] Not found → raises `AUTH_INVALID_KEY` 401 — L46-47
- [x] On success: `update(ApiKey).where(ApiKey.id == row.id).values(last_used_at=_now())` — L49-53
- [x] Returns `AuthenticatedUser(user_id, user_group_ids, auth_type="api_key")` — L56-59
- [x] Zero imports from `backend.rag` or `backend.api` (A001/A002)
- [x] Rule satisfied: S001 (ORM `.where()` — no f-string SQL)
- [x] Rule satisfied: S005 (no hardcoded secrets)

### Design note
Task spec says `WHERE is_active=TRUE` on `api_keys`, but `api_keys` table has no `is_active` column (S001 schema). Implementation correctly joins `User` and checks `User.is_active`. A deactivated user's keys are all invalid — correct design.

## T003: Tests — test_api_key.py

### Task Review Criteria
- [x] `test_missing_header_returns_401_auth_missing` — L47
- [x] `test_empty_header_returns_401_auth_missing` — L57
- [x] `test_invalid_hash_returns_401_auth_invalid_key` — L67
- [x] `test_inactive_key_returns_401_auth_invalid_key` — L77
- [x] `test_valid_key_returns_authenticated_user` — L88
- [x] `test_last_used_at_updated_on_success` — L102
- [x] `test_error_shape_has_request_id` — L115 (A005 compliance)
- [x] `test_no_rag_api_import` — L126 (A001 scope isolation)
- [x] All async tests use `pytest.mark.asyncio`
- [x] `AsyncMock` used for `db` parameter — no live DB
- [x] TDD: all auth paths exercised

## Security Checks
- [x] S001: Zero string interpolation in SQL — ORM `.where()` throughout
- [x] S003: Input sanitized — `.strip()` on header value
- [x] S005: No hardcoded secrets or URLs
- [x] A001: No cross-boundary imports (verified by test)
- [x] A002: Dependency direction auth → db only

## Full Checks
- [x] No magic numbers
- [x] No commented-out dead code
- [x] Docstrings on public functions
- [x] Test command passes — 8/8

## Issues Found

### ⚠️ WARNING — Minor (non-blocking)

1. **`_errors.py` L4+L14**: Stale comments say "fastapi added in S003" — fastapi was already added to `requirements.txt` during T003 implementation.

2. **`_errors.py` L6**: Unused import `Any` from typing.

3. **`api_key.py` L54**: `db.commit()` inside auth function — caller cannot control transaction boundaries. Acceptable for `last_used_at` update; may need refactoring when integrated in S004.

4. **`test_api_key.py` L14-17**: `try/except ImportError` fallback for HTTPException now unnecessary since fastapi is installed. Harmless defensive code.

## Verdict
**[x] APPROVED** [ ] CHANGES REQUIRED [ ] BLOCKED

Blockers: 0 | Warnings: 4 (minor) | Tests: 8/8 passed

## Task Status Summary

| Task | Status |
|------|--------|
| T001 | REVIEWED ✅ |
| T002 | REVIEWED ✅ |
| T003 | REVIEWED ✅ |

**Story S002 fully REVIEWED and APPROVED.**
