# Code Review: S004 — Unified verify_token FastAPI dependency
Level: security | Date: 2026-03-24 | Reviewer: Claude (opus)

---

## Task Review Criteria

### T001: AuthenticatedUser dataclass in types.py
- [x] `@dataclass(frozen=True)` decorator — immutable after creation
- [x] `user_id: uuid.UUID` field
- [x] `user_group_ids: list[int]` field
- [x] `auth_type: Literal["api_key", "oidc"]` field
- [x] No other fields, no methods, no business logic
- [x] File has spec reference header comment
- [x] Assignable test: `user.user_id = uuid.uuid4()` raises `FrozenInstanceError`
- [x] Rule satisfied: AC1 (immutable, correct field types)
- [x] api_key.py updated: removed temp class, imports from types.py
- [x] oidc.py updated: import redirected from api_key → types.py

### T002: verify_token + get_db in dependencies.py
- [x] `verify_token` signature uses FastAPI `Header()` for `x_api_key` (alias `"X-API-Key"`) and `authorization`
- [x] `x_api_key` check is FIRST (D05 — API-key takes precedence)
- [x] Bearer extraction: `authorization.removeprefix("Bearer ")` (Python 3.9+)
- [x] Neither header → `auth_error(request, "AUTH_MISSING", ..., 401)`
- [x] `get_db` uses `async with async_session_factory() as session: yield session`
- [x] Imports `async_session_factory` from `backend.db.session`
- [x] Imports `verify_api_key` from `backend.auth.api_key` and `verify_oidc_token` from `backend.auth.oidc`
- [x] Imports `AuthenticatedUser` from `backend.auth.types`
- [x] Rule satisfied: A002 (no reverse deps — auth imports from db only, not api/rag)
- [x] Rule satisfied: A005 (AUTH_MISSING error shape via _errors.py)

### T003: Update __init__.py public interface
- [x] `from .dependencies import verify_token` present
- [x] `from .types import AuthenticatedUser` present
- [x] `__all__ = ["verify_token", "AuthenticatedUser"]`
- [x] No export of `verify_api_key`, `verify_oidc_token`, `auth_error`, or `_errors`
- [x] Comment explaining why internal functions are intentionally unexported (AC5)
- [x] Rule satisfied: A001 (agent scope isolation — clean public interface)

### T004: Tests — test_dependencies.py + full suite
- [x] `test_api_key_header_takes_precedence_over_bearer` — both headers → `auth_type=="api_key"` (D05)
- [x] `test_bearer_only_dispatches_to_oidc` — only `Authorization: Bearer` → `auth_type=="oidc"`
- [x] `test_api_key_only_dispatches_to_api_key` — only `X-API-Key` → `auth_type=="api_key"`
- [x] `test_no_headers_returns_401_auth_missing` — neither header → 401 + `AUTH_MISSING`
- [x] `test_authenticated_user_is_frozen` — attempt field mutation → `FrozenInstanceError`
- [x] `test_authenticated_user_field_types` — `user_id` is UUID, `user_group_ids` is list, `auth_type` is str
- [x] `test_auth_module_not_exporting_internal_functions` — internal names not on `backend.auth`
- [x] `test_all_401_responses_conform_a005_shape` — 401 `detail` has `error.code`, `error.message`, `error.request_id`
- [x] Mocks use `unittest.mock.patch` on `backend.auth.dependencies.verify_api_key` etc.
- [x] No live DB — `get_db` dependency overridden in TestClient app
- [x] Rule satisfied: TDD (full suite passes)

---

## Full Checks
- [x] Error handling: AUTH_MISSING raised on no-auth path; sub-functions handle their own exceptions
- [x] No magic numbers (all constants from env or typed literals)
- [x] Docstring on `verify_token`, `get_db`, `AuthenticatedUser`
- [x] No commented-out dead code
- [x] No files outside TOUCH list modified (except conftest.py — test infra, justified below)

---

## Security Checks
- [x] S001: Zero string interpolation in SQL — no SQL in S004 files; sub-functions verified in S002/S003 reviews
- [x] S002: JWT validation delegated to verify_oidc_token (reviewed in S003) — no bypass in dispatcher
- [x] S005: No hardcoded secrets or URLs — all OIDC config from env vars
- [x] A005: AUTH_MISSING error via `auth_error()` helper — correct shape confirmed by test
- [x] No auth bypass: all three branches (api_key, bearer, neither) terminate in either verified AuthenticatedUser or 401
- [x] Header precedence (D05): API-key checked first — prevents OIDC fallback when bot sends both headers

---

## Issues Found

### ⚠️ WARNING — Minor (non-blocking)

1. ~~**dependencies.py L5: unused `TYPE_CHECKING` import**~~ — FIXED
2. **dependencies.py L20: `async_session_factory` may be `None`**
   If `DATABASE_URL` is unset, `async_session_factory` is `None` (per session.py L19). `get_db()` would raise `TypeError: 'NoneType' object does not support the context manager protocol`. This is acceptable in practice (tests override `get_db`, production requires `DATABASE_URL`), but a guarded error message would be clearer. Low priority.
3. **conftest.py: out of explicit TOUCH scope**
   `tests/auth/conftest.py` was not listed in any T001–T004 task TOUCH list. However, it is test infrastructure required for collection of the entire `tests/auth/` directory after `__init__.py` now transitively imports `oidc.py`. This is a justified scope addition — the alternative (duplicating env setup in every test file) is worse.
4. ~~**test_dependencies.py L145: unused `importlib` import**~~ — FIXED

---

## Verdict
[x] APPROVED  [ ] CHANGES REQUIRED  [ ] BLOCKED

No blockers. 4 minor warnings — none security-related. All 51 tests pass.
S004 story complete: 4/4 tasks REVIEWED.
