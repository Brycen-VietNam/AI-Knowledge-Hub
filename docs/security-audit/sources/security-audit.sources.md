# Sources Traceability: security-audit
Created: 2026-04-23 | Feature spec: `docs/security-audit/spec/security-audit.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Resolves two formally deferred security items from the `change-password` feature sprint:
DEFERRED-SEC-001 (password in authStore) and DEFERRED-SEC-002 (JWT session not invalidated on reset).

---

## AC-to-Source Mapping

### Story S001: Remove plaintext password from authStore — add refresh-token endpoint

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: POST /v1/auth/refresh endpoint exists | Existing behavior | `change-password` report — DEFERRED-SEC-001 entry | Identified as the correct mitigation: server issues refresh token so client no longer needs to remember password | 2026-04-22 |
| AC2: refresh returns access_token + refresh_token (TTLs: 15min/8h) | Business logic | Security team analysis — DEFERRED-SEC-001 memory record | 15-min access token minimizes exposure window; 8-hour refresh covers a standard workday | 2026-04-23 |
| AC3: /v1/auth/token returns refresh_token in response | Existing behavior | `backend/api/routes/auth.py` — current login response shape | Additive change only; existing `access_token` field preserved (C004 non-breaking) | 2026-04-13 |
| AC4: authStore.ts removes `password` field | Existing behavior | `frontend/src/store/authStore.ts` — `password` field currently present | DEFERRED-SEC-001 root cause; removing field closes XSS exfiltration vector | 2026-04-22 |
| AC5: ChangePasswordPage uses silent refresh instead of stored password | Existing behavior | `frontend/src/pages/ChangePasswordPage.tsx` — silent `authStore.password` usage | Current silent use is the exact security gap identified in DEFERRED-SEC-001 | 2026-04-22 |
| AC6: 401 on expired/invalid refresh token | Business logic | ARCH A005 — standard error shape; CONSTITUTION P005 (fail visibly) | Structured error with request_id required for all failure paths | 2026-03-18 |
| AC7: /v1/auth/refresh is not exempt from auth | Business logic | CONSTITUTION C003 / HARD R003 | Only /v1/health is anonymous; all other /v1/* require auth including refresh endpoint | 2026-03-18 |
| AC8: refresh token stored in memory only (not localStorage) | Business logic | Security team decision — session memory boundary | localStorage survives browser restart and tab share; memory-only limits exposure | 2026-04-23 |
| AC9: unit tests for refresh paths | Requirement doc | CONSTITUTION — Testing §: 80% coverage + integration tests for critical journeys | Auth endpoints are critical journeys — full coverage required | 2026-03-18 |
| AC10: no breaking change to /v1/auth/token and /v1/auth/change-password | Business logic | CONSTITUTION C004 — API versioning: breaking changes require /v2/ | Additive-only extension; no /v2/ bump needed | 2026-03-18 |

### Story S002: JWT session invalidation on admin password reset — token_version column

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: migration 012_add_token_version.sql | Business logic | HARD A006 + ARCH A006 | Schema changes must be migration-first; numbered file required before ORM update | 2026-03-18 |
| AC2: ORM User model adds token_version field | Existing behavior | `backend/db/models/user.py` — current model lacks token_version | ORM update follows migration review (A006) | 2026-04-21 |
| AC3: login embeds token_version in JWT | Business logic | DEFERRED-SEC-002 memory record — token_version approach | Version embedded at login time; stale sessions detected on next request without extra DB call | 2026-04-22 |
| AC4: verify_token rejects mismatched version (ERR_TOKEN_INVALIDATED) | Business logic | HARD R003 + ARCH A001 | verify_token is the correct enforcement boundary; consistent with existing auth middleware scope | 2026-03-18 |
| AC5: password_reset atomically increments token_version | Existing behavior | `backend/api/routes/admin.py` — password_reset handler | Atomic UPDATE prevents race condition between hash update and version increment | 2026-04-21 |
| AC6: old JWT returns 401 after reset | Conversation | `/clarify change-password` Q4 resolution | 60-min TTL accepted as risk at that time; token_version eliminates the window entirely | 2026-04-17 |
| AC7: new login after reset produces valid JWT with new version | Business logic | Logical consequence of AC3 + AC5 — derived from reset flow design | Expected behavior: login after reset uses new hash → produces JWT with incremented version | 2026-04-23 |
| AC8: no extra DB query in verify_token hot path | Business logic | PERF P004 (N+1 prevention) + HARD R007 (2s SLA) | User row already fetched for RBAC group_ids in verify_token — token_version read from same row | 2026-03-18 |
| AC9: unit tests for version matching and increment | Requirement doc | CONSTITUTION — Testing §: 80% coverage | Security path requires full test coverage | 2026-03-18 |
| AC10: admin password-reset API contract unchanged | Existing behavior | `backend/api/routes/admin.py` current contract + CONSTITUTION C004 | Only internal side-effect changes (token_version++) — request/response shape identical | 2026-04-21 |

---

## Summary

**Total ACs:** 20 (S001: 10, S002: 10)
**Fully traced:** 20/20 ✓
**Pending sources:** 0

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Requirement doc** | CONSTITUTION.md, HARD.md, PERF.md |
| **Existing behavior** | Current source files, API contracts, memory records |
| **Business logic** | BrSE analysis, security team decision, derived design constraint |
| **Conversation** | /clarify Q&A sessions, stakeholder decisions |
