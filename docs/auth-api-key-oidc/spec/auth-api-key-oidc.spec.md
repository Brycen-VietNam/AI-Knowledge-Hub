# Spec: auth-api-key-oidc
Created: 2026-03-23 | Author: /specify | Status: SPECCING

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | auth |
| Priority | P0 |
| Story count | 4 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 → S003 → S004 |
| Parallel-safe stories | S002, S003 (after S001 complete) |
| Blocking specs | rbac-document-filter, document-ingestion, query-endpoint |
| Blocked by | db-schema-embeddings (DONE ✅) |
| Agents needed | db-agent (S001), auth-agent (S002–S004) |

### Problem Statement
Knowledge-Hub không có auth layer — tất cả `/v1/*` endpoint đều anonymous, vi phạm C003 và R003.
Không có user_id → RBAC không resolve được `user_group_ids` → pgvector WHERE filter không hoạt động.
`audit_logs.user_id` hiện là TEXT placeholder, không có FK thực → audit log không hợp lệ về data integrity.

### Solution Summary
- Thêm `users` và `api_keys` tables; migrate `audit_logs.user_id` từ TEXT placeholder → UUID FK (S001)
- API-key middleware cho bots/service accounts: SHA-256 hash lookup, `verify_api_key()` (S002)
- OIDC/JWT Bearer middleware cho human users: PyJWT RS256/ES256, JWKS TTL cache, JIT user provisioning (S003)
- Unified `verify_token` FastAPI dependency: dispatch API-key ↔ OIDC, trả về `AuthenticatedUser` (S004)
- Toàn bộ logic trong `backend/auth/`; public interface duy nhất: `verify_token` + `AuthenticatedUser`

### Out of Scope
- Rate limiting enforcement (spec riêng: `rate-limiting`, đọc `auth_type` từ `AuthenticatedUser`)
- RBAC permission resolution ngoài việc return `user_group_ids` (rag-agent scope)
- Admin CRUD cho users/groups (admin-api spec tương lai)
- Keycloak realm setup / infrastructure provisioning

---

## LAYER 2 — Story Detail

---

### S001: Users table + API-key schema migration

**Role / Want / Value**
- As a: db-agent
- I want: `users` table với OIDC sub claim support và `api_keys` table với hash-based key storage
- So that: auth-agent có DB foundation để lưu user identities và API keys, và `audit_logs.user_id` là real FK thay vì TEXT placeholder

**Acceptance Criteria**
- [ ] AC1: Table `users(id UUID PK DEFAULT gen_random_uuid(), sub TEXT UNIQUE NOT NULL, email TEXT, display_name TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT now())` tồn tại. `sub` lưu OIDC `sub` claim (hoặc synthetic sub cho API-key service accounts theo format `svc:<description>`). `email` và `display_name` là **NULLABLE** (một số OIDC providers không include email/name claim).
- [ ] AC2: Table `api_keys(id UUID PK DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, key_hash TEXT NOT NULL UNIQUE, description TEXT, user_group_ids INTEGER[] NOT NULL DEFAULT '{}', is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), last_used_at TIMESTAMPTZ)` tồn tại. Không có column `key_plaintext`.
- [ ] AC3: `audit_logs.user_id` được ALTER từ `TEXT NOT NULL` thành `UUID NOT NULL REFERENCES users(id)`. Migration tạo sentinel user `(sub='__migration_placeholder__')` trước khi apply FK constraint để existing rows có valid FK.
- [ ] AC4: Migration file là `backend/db/migrations/004_create_users_api_keys.sql` với FORWARD section và ROLLBACK section (commented SQL ở cuối file). Rollback reverse FK, drop `api_keys`, drop `users` theo đúng dependency order.
- [ ] AC5: ORM models `backend/db/models/user.py` (`User`) và `backend/db/models/api_key.py` (`ApiKey`) được tạo sau khi migration review. `backend/db/models/__init__.py` export cả hai. `AuditLog.user_id` Mapped column type cập nhật từ `str` → `uuid.UUID` với FK declared.

**API Contract** — N/A (DB migration only, executed at deploy time)

**Auth Requirement**
- [ ] OIDC Bearer (human)  [ ] API-Key (bot)  [x] N/A — schema level

**Non-functional**
- Latency: migration runs once at deploy — not on critical path
- Audit log: schema correctness là deliverable
- CJK support: not applicable

**Implementation notes**
- `users.sub` format cho API-key accounts: `svc:<key_description>` (synthetic, không clash với real OIDC sub)
- `api_keys.user_group_ids` là `INTEGER[]` (PostgreSQL array) — cùng type với `user_groups.id`
- Migration 004 phụ thuộc migrations 001–003; thêm `-- Requires: migrations 001, 002, 003 applied` ở header
- Dùng `gen_random_uuid()` cho tất cả UUID PKs — consistent với migration 001 pattern
- Follow `Identity()` pattern không dùng cho UUID PKs (UUID dùng `gen_random_uuid()`)
- Existing test pattern: `tests/db/test_models.py` dùng SQLite in-memory engine + `inspect()` cho FK verification

---

### S002: API-key authentication middleware

**Role / Want / Value**
- As a: api-agent (bot/service account consumer)
- I want: FastAPI-compatible `verify_api_key` function validates `X-API-Key` header against `api_keys` table
- So that: bots và service accounts authenticate mà không cần OIDC, và `user_id` + `user_group_ids` được resolved cho RBAC

**Acceptance Criteria**
- [ ] AC1: `verify_api_key(request: Request, db: AsyncSession) -> AuthenticatedUser` hash SHA-256 incoming `X-API-Key` header và lookup `api_keys.key_hash`. Trả về `AuthenticatedUser(user_id=..., user_group_ids=[...], auth_type="api_key")` khi thành công.
- [ ] AC2: `X-API-Key` header vắng mặt hoặc rỗng → raise `HTTPException(status_code=401, detail={"error": {"code": "AUTH_MISSING", "message": "Authentication required", "request_id": "<uuid>"}})`.
- [ ] AC3: `key_hash` không tìm thấy trong DB hoặc `is_active = FALSE` → raise `HTTPException(status_code=401, detail={"error": {"code": "AUTH_INVALID_KEY", "message": "Invalid or revoked API key", "request_id": "<uuid>"}})`. Stack trace không bao giờ exposed trong response.
- [ ] AC4: Khi validate thành công, `api_keys.last_used_at` được UPDATE thành `now()` trong cùng DB session.
- [ ] AC5: `backend/auth/api_key.py` chỉ import từ `backend/db/` (via `AsyncSession` và model queries). Không import từ `backend/rag/` hoặc `backend/api/`.

**API Contract**
```
Tất cả /v1/* endpoints (ngoại trừ /v1/health)
Headers: X-API-Key: <plaintext_key>
On success: request proceeds with AuthenticatedUser injected
Response 401: {"error": {"code": "AUTH_MISSING|AUTH_INVALID_KEY", "message": "...", "request_id": "<uuid>"}}
```

**Auth Requirement**
- [ ] OIDC Bearer (human)  [x] API-Key (bot)  [ ] Both

**Non-functional**
- Latency: single indexed DB lookup trên `key_hash` (TEXT UNIQUE) — expected < 5ms
- Audit log: `last_used_at` update là audit mechanism cho API-key access
- CJK support: not applicable

**Implementation notes**
- Hash: `hashlib.sha256(key.encode()).hexdigest()` — Python stdlib, không cần thêm dependency
- `request_id` trong error responses: dùng `request.state.request_id` nếu có, else `str(uuid.uuid4())`
- DB query: `SELECT ... WHERE key_hash = :hash AND is_active = TRUE` — parameterized (S001 SQL injection prevention)
- File: `backend/auth/api_key.py`; test: `tests/auth/test_api_key.py`

---

### S003: OIDC/JWT Bearer authentication middleware

**Role / Want / Value**
- As a: api-agent (human user consumer via Web SPA, Teams bot, Slack bot)
- I want: FastAPI-compatible `verify_oidc_token` function validates `Bearer` JWT against OIDC issuer's JWKS endpoint
- So that: human users authenticated qua Keycloak có thể access `/v1/*` endpoints với group memberships resolved

**Acceptance Criteria**
- [ ] AC1: `verify_oidc_token(request: Request, token: str, db: AsyncSession) -> AuthenticatedUser` validate: (a) JWT signature RS256/ES256 against JWKS public key, (b) `exp` claim trong tương lai, (c) `iss` claim == `OIDC_ISSUER` env var, (d) `aud` claim == `OIDC_AUDIENCE` env var. Groups claim (list of strings) → DB lookup `user_groups.name IN (...)` → resolve `user_group_ids`. Nếu `groups` claim absent hoặc empty → `user_group_ids=[]` (permissive, không 403). JIT UPSERT vào `users` table theo `sub` claim; `email` lấy từ claim tên bởi `OIDC_EMAIL_CLAIM` env var (default `"email"`), `display_name` từ `OIDC_NAME_CLAIM` env var (default `"name"`). Trả về `AuthenticatedUser(user_id=users.id, user_group_ids=[...], auth_type="oidc")`.
- [ ] AC2: JWKS public keys được fetch từ `OIDC_JWKS_URI` env var và cached in-process với TTL configurable qua `OIDC_JWKS_CACHE_TTL_SECONDS` (default 3600s). Cache được refresh khi TTL hết hoặc khi `kid` không tìm thấy trong cache (support key rotation không cần restart).
- [ ] AC3: `Authorization` header vắng mặt hoặc không phải format `Bearer <token>` → raise `HTTPException(status_code=401, detail={"error": {"code": "AUTH_MISSING", "message": "Authentication required", "request_id": "<uuid>"}})`.
- [ ] AC4: Bất kỳ JWT validation failure nào (expired, bad signature, wrong issuer, wrong audience) → raise `HTTPException(status_code=401, detail={"error": {"code": "AUTH_TOKEN_INVALID", "message": "Token validation failed", "request_id": "<uuid>"}})`. Token contents, internal exception messages, và JWKS fetch errors không bao giờ exposed trong response body.
- [ ] AC5: `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URI` được đọc từ environment variables. Nếu bất kỳ env var nào missing khi startup → `RuntimeError("Missing required env var: <VAR_NAME>")` được raise trước khi nhận request. `OIDC_GROUPS_CLAIM` env var (default `"groups"`) cấu hình tên claim chứa group names.

**API Contract**
```
Tất cả /v1/* endpoints (ngoại trừ /v1/health)
Headers: Authorization: Bearer <jwt_token>
On success: request proceeds with AuthenticatedUser injected
Response 401: {"error": {"code": "AUTH_MISSING|AUTH_TOKEN_INVALID", "message": "...", "request_id": "<uuid>"}}
```

**Auth Requirement**
- [x] OIDC Bearer (human)  [ ] API-Key (bot)  [ ] Both

**Non-functional**
- Latency: JWKS cache hit path < 2ms (in-memory lookup + PyJWT decode). JWKS HTTP fetch có timeout 2s.
- Audit log: `user_id` extracted từ `sub` claim → passed cho audit log bởi api-agent (không log trong verify_oidc_token)
- CJK support: not applicable (auth layer, không xử lý query content)

**Implementation notes**
- Library: `PyJWT >= 2.8` với `cryptography` extra — `pip install PyJWT[cryptography]`
- JWKS async fetch: `httpx.AsyncClient` với `timeout=2.0`
- JWKS cache structure: `dict[str, Any]` keyed by `kid` (JWT header key ID) → fast lookup
- JIT provisioning: `INSERT INTO users (sub, email, display_name) VALUES (:sub, :email, :name) ON CONFLICT (sub) DO UPDATE SET email=EXCLUDED.email, display_name=EXCLUDED.display_name`
- Groups DB lookup: `SELECT id FROM user_groups WHERE name = ANY(:names)` — parameterized array query
- File: `backend/auth/oidc.py`; test: `tests/auth/test_oidc.py`
- New dependencies (thêm vào `requirements.txt`): `PyJWT>=2.8.0`, `cryptography>=42.0.0`, `httpx>=0.27.0`

---

### S004: Unified `verify_token` FastAPI dependency

**Role / Want / Value**
- As a: api-agent (tất cả route authors)
- I want: single `verify_token` FastAPI dependency hoạt động cho cả API-key và OIDC Bearer tokens mà không cần branching tại route level
- So that: tất cả `/v1/*` routes chỉ cần đúng 1 `Depends(verify_token)` và nhận `AuthenticatedUser` object bất kể auth method

**Acceptance Criteria**
- [ ] AC1: `AuthenticatedUser` frozen dataclass (hoặc Pydantic `model_config = ConfigDict(frozen=True)`) được định nghĩa với fields: `user_id: uuid.UUID`, `user_group_ids: list[int]`, `auth_type: Literal["api_key", "oidc"]`. Immutable — mutating field raises `FrozenInstanceError` hoặc equivalent.
- [ ] AC2: `verify_token(request: Request, x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)) -> AuthenticatedUser` dispatch dựa trên header: `X-API-Key` present → gọi `verify_api_key`; `Authorization: Bearer` present → gọi `verify_oidc_token`; không có header nào → raise 401 `AUTH_MISSING`.
- [ ] AC3: Nếu cả `X-API-Key` và `Authorization: Bearer` đều present, `X-API-Key` takes precedence. Behavior này được document trong function docstring.
- [ ] AC4: Tất cả auth error responses conform A005 shape: `{"error": {"code": str, "message": str, "request_id": str}}` với `request_id` là valid UUID string. Error codes: `AUTH_MISSING` (401), `AUTH_INVALID_KEY` (401), `AUTH_TOKEN_INVALID` (401), `AUTH_FORBIDDEN` (403).
- [ ] AC5: `backend/auth/__init__.py` export ONLY `verify_token` và `AuthenticatedUser`. `verify_api_key` và `verify_oidc_token` là internal — `from backend.auth import verify_api_key` phải raise `ImportError`.

**API Contract**
```
Usage trong routes:
@router.post("/v1/query", dependencies=[Depends(verify_token)])
async def query(user: AuthenticatedUser = Depends(verify_token), ...):
    # user.user_id, user.user_group_ids, user.auth_type available

Response 401: {"error": {"code": "AUTH_MISSING|AUTH_INVALID_KEY|AUTH_TOKEN_INVALID", "message": "...", "request_id": "<uuid>"}}
Response 403: {"error": {"code": "AUTH_FORBIDDEN", "message": "...", "request_id": "<uuid>"}}
```

**Auth Requirement**
- [x] OIDC Bearer (human) — dispatched via `verify_oidc_token`
- [x] API-Key (bot) — dispatched via `verify_api_key`

**Non-functional**
- Latency: `verify_token` overhead < 1ms (header inspection only); actual latency là S002/S003's responsibility
- Audit log: `user.user_id` passed bởi api-agent cho `audit_logs` — không log trong `verify_token` (giữ auth module stateless cho testing)
- CJK support: not applicable

**Implementation notes**
- `get_db` session dependency: import từ `backend.db.session` — permitted cross-boundary import (auth → db)
- Integration test: spin up minimal FastAPI app với test route dùng `Depends(verify_token)`, assert cả hai auth paths succeed end-to-end
- File: `backend/auth/dependencies.py`; test: `tests/auth/test_dependencies.py`
- `tests/auth/__init__.py` phải được tạo (empty) để auth test package importable

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Requirement doc | CONSTITUTION.md C003 (all /v1/* require auth — needs user identity) | 2026-03-23 |
| AC1 | Requirement doc | SECURITY.md S002 (JWT sub claim = primary user identifier) | 2026-03-23 |
| AC2 | Requirement doc | HARD.md R003 (every endpoint requires auth — API-key is valid mechanism) | 2026-03-23 |
| AC2 | Requirement doc | SECURITY.md S005 (zero hardcoded secrets — key_hash only, no plaintext) | 2026-03-23 |
| AC3 | Requirement doc | CONSTITUTION.md C008 (audit log requires user_id) | 2026-03-23 |
| AC3 | Existing behavior | `backend/db/migrations/001_create_core_schema.sql` comment: "FK added by auth-agent" | 2026-03-23 |
| AC4 | Requirement doc | CONSTITUTION.md C010 (numbered migration with rollback section) | 2026-03-23 |
| AC4 | Requirement doc | ARCH.md A006 (migration strategy: numbered files, rollback required) | 2026-03-23 |
| AC5 | Requirement doc | CONSTITUTION.md C010 (ORM updated after migration review) | 2026-03-23 |
| AC5 | Existing behavior | `backend/db/models/__init__.py` export convention (session 2026-03-18) | 2026-03-23 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Requirement doc | HARD.md R003 (Depends(verify_token) pattern) | 2026-03-23 |
| AC1 | Requirement doc | SECURITY.md S005 (no plaintext key storage — SHA-256 hash) | 2026-03-23 |
| AC2 | Requirement doc | ARCH.md A005 (error response shape: code + message + request_id) | 2026-03-23 |
| AC2 | Requirement doc | HARD.md R003 (no anonymous access to /v1/*) | 2026-03-23 |
| AC3 | Requirement doc | ARCH.md A005 (structured errors, no stack traces) | 2026-03-23 |
| AC3 | Requirement doc | SECURITY.md S001 (no internal paths exposed in production) | 2026-03-23 |
| AC4 | Business logic | Key usage audit for service account monitoring | 2026-03-23 |
| AC5 | Requirement doc | ARCH.md A001 (agent scope isolation — auth-agent owns backend/auth/) | 2026-03-23 |
| AC5 | Requirement doc | ARCH.md A002 (dependency direction: api → auth → db; never auth → rag) | 2026-03-23 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Requirement doc | SECURITY.md S002 (verify: signature, expiry, issuer, audience on EVERY request) | 2026-03-23 |
| AC1 | Requirement doc | HARD.md R003 (no anonymous access to /v1/*) | 2026-03-23 |
| AC1 | Requirement doc | CONSTITUTION.md C003 (Bearer is valid auth mechanism for humans) | 2026-03-23 |
| AC1 | Conversation | Q&A 2026-03-23 — D01: groups claim = names (strings), DB lookup required | 2026-03-23 |
| AC1 | Conversation | Q&A 2026-03-23 — D02: JIT user provisioning on first OIDC login | 2026-03-23 |
| AC2 | Requirement doc | SECURITY.md S002 ("Cache public keys with TTL, not forever") | 2026-03-23 |
| AC2 | Requirement doc | SECURITY.md S005 (OIDC_JWKS_URI phải là env var) | 2026-03-23 |
| AC3 | Requirement doc | ARCH.md A005 (error response shape) | 2026-03-23 |
| AC4 | Requirement doc | ARCH.md A005 (no stack traces in error response) | 2026-03-23 |
| AC4 | Requirement doc | SECURITY.md S002 (all 4 JWT claims validated — any failure = 401) | 2026-03-23 |
| AC5 | Requirement doc | SECURITY.md S005 (zero hardcoded secrets — all via env vars) | 2026-03-23 |
| AC5 | Requirement doc | CONSTITUTION.md Non-Negotiables: "Zero hardcoded secrets in source code" | 2026-03-23 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Requirement doc | HARD.md R003 (verify_token returns unified identity) | 2026-03-23 |
| AC1 | Requirement doc | ARCH.md A001 (interface defined in auth scope, consumed by api-agent) | 2026-03-23 |
| AC2 | Requirement doc | HARD.md R003 (single Depends(verify_token) on all routes) | 2026-03-23 |
| AC2 | Requirement doc | CONSTITUTION.md C003 (no anonymous access to /v1/*) | 2026-03-23 |
| AC3 | Business logic | API-key precedence when both headers present — documented behavior, Q&A 2026-03-23 | 2026-03-23 |
| AC4 | Requirement doc | ARCH.md A005 (error response shape: exactly code + message + request_id) | 2026-03-23 |
| AC4 | Requirement doc | CONSTITUTION.md P005 (fail fast, fail visibly — structured errors) | 2026-03-23 |
| AC5 | Requirement doc | ARCH.md A001 (auth module public interface: only verify_token + AuthenticatedUser) | 2026-03-23 |
| AC5 | Requirement doc | ARCH.md A002 (api-agent imports from auth/ only via interface) | 2026-03-23 |

---
