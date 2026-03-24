# Plan: auth-api-key-oidc
Generated: 2026-03-23 | Feature branch: feature/auth

---

## Context
The Knowledge-Hub API requires authentication before any `/v1/*` endpoints can be built. Currently `backend/auth/` does not exist. This sprint implements the full auth layer: DB schema for users/API keys, API-key middleware, OIDC/JWT middleware, and a unified `verify_token` FastAPI dependency. This unblocks `rbac-document-filter`, `document-ingestion`, and `query-endpoint` sprints.

Checklist status: **WARN-approved** (24/26 pass, 2 WARNs auto-approved as N/A).

---

## Layer 1 — Summary

```
Stories: 4 | Est. sessions: 2 | Critical path: S001 → S002 → S003 → S004
Token budget total: ~4,100 tokens

Group 1 (serial):       S001 — db-agent
Group 2 (sequential):   S002 → S003 — auth-agent (after G1)
Group 3 (serial):       S004 — auth-agent (after G2)

NOTE: auth-agent is ALWAYS sequential per AGENTS.md. S002/S003 are
      logically parallel-safe but executed sequentially by the same agent.
```

Critical path diagram:
```
[db-schema-embeddings DONE ✅]
           │
    ┌──────▼──────┐
    │    S001     │  db-agent
    │  DB schema  │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │    S002     │  auth-agent (first)
    │   API key   │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │    S003     │  auth-agent (second)
    │    OIDC     │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │    S004     │  auth-agent (third)
    │ verify_token│
    └─────────────┘
           │
    [UNBLOCKS: rbac, ingestion, query]
```

---

## Layer 2 — Per-Story Plans

---

### S001: Users table + API-key schema migration
**Agent:** db-agent | **Group:** G1 (serial, must complete first)

**Files to CREATE:**

`backend/db/migrations/004_create_users_api_keys.sql`
- Forward section (in dependency order):
  1. `CREATE TABLE users` — UUID PK via `gen_random_uuid()`, `sub TEXT UNIQUE NOT NULL`, `email TEXT` nullable, `display_name TEXT` nullable, `is_active BOOLEAN DEFAULT TRUE`, `created_at TIMESTAMPTZ DEFAULT now()`
  2. `CREATE TABLE api_keys` — UUID PK, `user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE`, `key_hash TEXT NOT NULL UNIQUE`, `description TEXT` nullable, `user_group_ids INTEGER[] NOT NULL DEFAULT '{}'`, `is_active BOOLEAN DEFAULT TRUE`, `created_at TIMESTAMPTZ DEFAULT now()`, `last_used_at TIMESTAMPTZ` nullable
  3. Index: `CREATE INDEX idx_users_sub ON users(sub)`
  4. `ALTER TABLE audit_logs ALTER COLUMN user_id TYPE UUID USING user_id::uuid` (table is EMPTY per D08 — no UPDATE needed)
  5. `ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID`
  6. `ALTER TABLE audit_logs VALIDATE CONSTRAINT fk_audit_logs_user`
- Rollback section (commented at bottom, reverse order)
- Header: `-- Requires: migrations 001, 002, 003 applied`

`backend/db/models/user.py`
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sub: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(nullable=True)
    display_name: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
```

`backend/db/models/api_key.py`
```python
class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    user_group_ids: Mapped[list] = mapped_column(ARRAY(INTEGER), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
```

`tests/db/test_auth_models.py` — follow pattern from `tests/db/test_models.py`; use SQLite in-memory engine.
Key tests: `test_user_sub_unique`, `test_api_key_no_plaintext`, `test_api_key_user_group_ids_default`, `test_audit_log_fk_to_users`, `test_models_init_exports_auth`

**Files to MODIFY:**

`backend/db/models/audit_log.py`
- Change `user_id: Mapped[str]` → `Mapped[uuid.UUID]`
- Add `ForeignKey("users.id")` to `mapped_column`

`backend/db/models/__init__.py`
- Add `from .user import User` and `from .api_key import ApiKey`
- Add `"User"`, `"ApiKey"` to `__all__`

`tests/db/test_models.py`
- **BREAKING:** `test_audit_log_user_id_is_text` (L123) will fail after ORM change
- Update: replace `user_id="auth0|some-user-id-placeholder"` with `user_id=uuid.uuid4()`; update assertion

**ARCH rule:** Migration file FIRST, ORM models SECOND (A006). db-agent must not create ORM before migration is reviewed.

**⚠️ SQLite caveat:** `ARRAY(INTEGER)` is PostgreSQL-specific. In SQLite tests, skip `user_group_ids` column dialect checks or use `@pytest.mark.skipif` on dialect.

**Test command:** `pytest tests/db/test_auth_models.py tests/db/test_models.py -v`

---

### S002: API-key authentication middleware
**Agent:** auth-agent | **Group:** G2 (first, after S001)

**Files to CREATE:**

`backend/auth/__init__.py` — empty placeholder (replaced in S004)

`backend/auth/_errors.py` — shared error helper (avoids duplication across S002/S003/S004):
```python
def auth_error(request: Request, code: str, message: str, status: int) -> HTTPException:
    rid = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    return HTTPException(status_code=status,
        detail={"error": {"code": code, "message": message, "request_id": rid}})
```

`backend/auth/api_key.py`
```python
async def verify_api_key(request: Request, db: AsyncSession) -> "AuthenticatedUser":
    key = request.headers.get("X-API-Key")
    if not key:
        raise auth_error(request, "AUTH_MISSING", "Authentication required", 401)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    # SELECT from api_keys WHERE key_hash=:hash AND is_active=TRUE
    # Not found → AUTH_INVALID_KEY
    # Found → UPDATE last_used_at=now(), return AuthenticatedUser(auth_type="api_key")
```
- Only imports: `backend.db.models.api_key`, `backend.db.models.user`, `backend.auth._errors`
- **Zero imports from** `backend.rag` or `backend.api` (A001/A002)

`tests/auth/__init__.py` — empty
`tests/auth/test_api_key.py` — 7 tests using `AsyncMock` for session:
- `test_missing_header_401_auth_missing`
- `test_empty_header_401_auth_missing`
- `test_invalid_hash_401_auth_invalid_key`
- `test_inactive_key_401_auth_invalid_key`
- `test_valid_key_returns_authenticated_user` (auth_type=="api_key")
- `test_last_used_at_updated_on_success`
- `test_no_rag_import` — assert `"backend.rag"` not in `sys.modules` after import

**Test command:** `pytest tests/auth/test_api_key.py -v`

---

### S003: OIDC/JWT Bearer authentication middleware
**Agent:** auth-agent | **Group:** G2 (second, after S002)

**New dependencies** (add to `requirements.txt` at start of this story):
```
PyJWT>=2.8.0
cryptography>=42.0.0
httpx>=0.27.0
```

**Files to CREATE:**

`backend/auth/oidc.py` — three responsibilities:

1. **Module-level startup validation:**
```python
_REQUIRED = ["OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URI"]
for _v in _REQUIRED:
    if not os.getenv(_v):
        raise RuntimeError(f"Missing required env var: {_v}")
OIDC_ISSUER = os.getenv("OIDC_ISSUER")
# ... + OIDC_AUDIENCE, OIDC_JWKS_URI, OIDC_GROUPS_CLAIM (default "groups"),
#         OIDC_EMAIL_CLAIM (default "email"), OIDC_NAME_CLAIM (default "name"),
#         OIDC_JWKS_CACHE_TTL (default 3600)
```

2. **JWKS cache** (module-level dict, not per-request):
```python
_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0

async def _get_jwks_key(kid: str) -> Any:
    if kid not in _jwks_cache or (time.monotonic() - _jwks_fetched_at) > OIDC_JWKS_CACHE_TTL:
        await _refresh_jwks_cache()
    return _jwks_cache.get(kid)  # None → caller raises AUTH_TOKEN_INVALID
```
httpx timeout: 2.0s

3. **Per-request validation:**
```python
async def verify_oidc_token(request: Request, token: str, db: AsyncSession) -> "AuthenticatedUser":
    try:
        header = jwt.get_unverified_header(token)
        key = await _get_jwks_key(header.get("kid"))
        if key is None: raise InvalidKeyError(...)
        payload = jwt.decode(token, key, algorithms=["RS256","ES256"],
            audience=OIDC_AUDIENCE, issuer=OIDC_ISSUER,
            options={"require": ["exp","iss","aud","sub"]})
    except Exception:
        raise auth_error(request, "AUTH_TOKEN_INVALID", "Token validation failed", 401)

    sub = payload["sub"]
    group_names: list[str] = payload.get(OIDC_GROUPS_CLAIM) or []  # D06: empty = []
    user_id = await _jit_upsert_user(db, sub, payload.get(OIDC_EMAIL_CLAIM), payload.get(OIDC_NAME_CLAIM))
    user_group_ids = await _resolve_group_ids(db, group_names) if group_names else []
    return AuthenticatedUser(user_id=user_id, user_group_ids=user_group_ids, auth_type="oidc")
```

JIT UPSERT via `text()` with named params (S001 SQL injection rule):
```sql
INSERT INTO users (sub, email, display_name) VALUES (:sub, :email, :display_name)
ON CONFLICT (sub) DO UPDATE SET email=EXCLUDED.email, display_name=EXCLUDED.display_name
RETURNING id
```

Groups resolution via ORM `UserGroup.name.in_(group_names)` — parameterized (S001 rule).

`tests/auth/test_oidc.py` — 13 tests; fixtures use `monkeypatch.setenv` for all OIDC env vars + RSA key pair generated via `cryptography`:
- `test_missing_env_var_raises_runtime_error`
- `test_valid_bearer_returns_authenticated_user`
- `test_expired_token_401`
- `test_wrong_issuer_401`
- `test_wrong_audience_401`
- `test_bad_signature_401`
- `test_unknown_kid_refreshes_then_fails_401`
- `test_empty_groups_returns_empty_list` (D06)
- `test_absent_groups_returns_empty_list` (D06)
- `test_jit_upsert_called_on_new_user`
- `test_jit_upsert_updates_email_on_return`
- `test_error_does_not_expose_token_content` (AC4)
- `test_jwks_cache_ttl_respected`

**Test command:** `pytest tests/auth/test_oidc.py -v`

---

### S004: Unified `verify_token` FastAPI dependency
**Agent:** auth-agent | **Group:** G3 (after G2)

**Files to CREATE:**

`backend/auth/types.py` — defines `AuthenticatedUser` to avoid circular imports:
```python
from dataclasses import dataclass
from typing import Literal
import uuid

@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: uuid.UUID
    user_group_ids: list[int]
    auth_type: Literal["api_key", "oidc"]
```
Both `api_key.py` and `oidc.py` import `AuthenticatedUser` from here.

`backend/auth/dependencies.py`
```python
async def verify_token(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    if x_api_key:                                          # D05: API-key takes precedence
        return await verify_api_key(request, db)
    if authorization and authorization.startswith("Bearer "):
        return await verify_oidc_token(request, authorization[7:], db)
    raise auth_error(request, "AUTH_MISSING", "Authentication required", 401)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```
Imports `async_session_factory` from `backend.db.session` (the existing session factory).

`tests/auth/test_dependencies.py` — 8 tests using `TestClient` with minimal FastAPI app:
- `test_api_key_precedence_over_bearer` (D05)
- `test_bearer_only_routes_to_oidc`
- `test_api_key_only_routes_to_api_key`
- `test_no_headers_401_auth_missing`
- `test_authenticated_user_is_frozen`
- `test_authenticated_user_field_types`
- `test_auth_module_not_exporting_internal_functions` (AC5)
- `test_all_401_responses_conform_a005_shape`

**Files to MODIFY:**

`backend/auth/__init__.py` — replace placeholder:
```python
from .dependencies import verify_token
from .types import AuthenticatedUser
__all__ = ["verify_token", "AuthenticatedUser"]
# verify_api_key, verify_oidc_token intentionally NOT exported (AC5)
```

**Test command:** `pytest tests/auth/ -v`

---

## Rule Compliance Checks

| Rule | Check command |
|------|---------------|
| A001 (scope isolation) | `grep -rn "from backend.rag\|from backend.api" backend/auth/` → 0 matches |
| A005 (error shape) | `test_all_401_responses_conform_a005_shape` in test_dependencies.py |
| R003 (auth on endpoints) | Enforced at api-agent sprint — not applicable yet |
| S001 (SQL injection) | `grep -rn 'f"' backend/auth/` → 0 matches; all queries use parameterized text() or ORM |
| S002 (JWT all 4 claims) | Tests: `test_expired_token_401`, `test_wrong_issuer_401`, `test_wrong_audience_401`, `test_bad_signature_401` |
| S005 (no hardcoded secrets) | `grep -rn '"http\|"postgres\|api_key\s*=' backend/auth/` → 0 matches |

---

## File Summary

| Action | File | Story | Agent |
|--------|------|-------|-------|
| CREATE | `backend/db/migrations/004_create_users_api_keys.sql` | S001 | db-agent |
| CREATE | `backend/db/models/user.py` | S001 | db-agent |
| CREATE | `backend/db/models/api_key.py` | S001 | db-agent |
| MODIFY | `backend/db/models/audit_log.py` | S001 | db-agent |
| MODIFY | `backend/db/models/__init__.py` | S001 | db-agent |
| MODIFY | `tests/db/test_models.py` L123–141 | S001 | db-agent |
| CREATE | `tests/db/test_auth_models.py` | S001 | db-agent |
| CREATE | `backend/auth/__init__.py` (placeholder) | S002 | auth-agent |
| CREATE | `backend/auth/_errors.py` | S002 | auth-agent |
| CREATE | `backend/auth/api_key.py` | S002 | auth-agent |
| CREATE | `tests/auth/__init__.py` | S002 | auth-agent |
| CREATE | `tests/auth/test_api_key.py` | S002 | auth-agent |
| CREATE | `backend/auth/oidc.py` | S003 | auth-agent |
| MODIFY | `requirements.txt` | S003 | auth-agent |
| CREATE | `tests/auth/test_oidc.py` | S003 | auth-agent |
| CREATE | `backend/auth/types.py` | S004 | auth-agent |
| CREATE | `backend/auth/dependencies.py` | S004 | auth-agent |
| MODIFY | `backend/auth/__init__.py` | S004 | auth-agent |
| CREATE | `tests/auth/test_dependencies.py` | S004 | auth-agent |

**Total:** 14 new files, 5 modified files

---

## Verification — End-to-End

```bash
# 1. Run migration (requires live PostgreSQL)
psql $DATABASE_URL -f backend/db/migrations/004_create_users_api_keys.sql

# 2. Verify schema
psql $DATABASE_URL -c "\d users"
psql $DATABASE_URL -c "\d api_keys"
psql $DATABASE_URL -c "\d audit_logs"  # confirm user_id is UUID FK

# 3. Run all tests
pytest tests/db/ tests/auth/ -v

# 4. Scope check
grep -rn "from backend.rag\|from backend.api" backend/auth/   # → 0 matches
grep -rn 'f"WHERE\|f"SELECT\|f"INSERT' backend/auth/          # → 0 matches
```

---

## Dispatch Packages (for /tasks)

```markdown
## DISPATCH: db-agent | Task: T001
CONTEXT: auth-api-key-oidc sprint — create users/api_keys tables and update audit_logs FK
CONSTRAINT: A006 (migration before ORM), S001 (no SQL injection), A001 (db-agent owns backend/db/)
TASK: Create 004_create_users_api_keys.sql, user.py, api_key.py; update audit_log.py + __init__.py; fix test_models.py
TOUCH: [backend/db/migrations/, backend/db/models/, tests/db/]
NO_TOUCH: [backend/auth/, backend/api/, backend/rag/]
TEST_CMD: pytest tests/db/test_auth_models.py tests/db/test_models.py -v
MEMORY: .claude/memory/WARM/auth-api-key-oidc.mem.md

## DISPATCH: auth-agent | Task: T002+T003+T004
CONTEXT: auth-api-key-oidc sprint — implement API-key + OIDC middleware + unified verify_token; S001 must be DONE first
CONSTRAINT: A001 (no rag/api imports), A005 (error shape), S005 (no hardcoded secrets), S002 (JWT: sig+exp+iss+aud)
TASK: Create _errors.py, api_key.py, oidc.py, types.py, dependencies.py; update __init__.py; add PyJWT/cryptography/httpx to requirements.txt
TOUCH: [backend/auth/, tests/auth/, requirements.txt]
NO_TOUCH: [backend/db/, backend/rag/, backend/api/]
TEST_CMD: pytest tests/auth/ -v
MEMORY: .claude/memory/WARM/auth-api-key-oidc.mem.md
```
