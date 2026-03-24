# Sources Traceability: auth-api-key-oidc
Created: 2026-03-23 | Feature spec: `docs/specs/auth-api-key-oidc.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Users table + API-key schema migration

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: users table schema | Requirement doc | CONSTITUTION.md C003 | All /v1/* require auth — needs user identity table with sub claim | 2026-03-23 |
| AC1: sub claim format | Requirement doc | SECURITY.md S002 | JWT sub claim = primary user identifier; synthetic `svc:` prefix for API-key accounts | 2026-03-23 |
| AC2: api_keys table, key_hash only | Requirement doc | SECURITY.md S005 | Zero hardcoded secrets — plaintext key never stored; SHA-256 hash only | 2026-03-23 |
| AC2: api_keys.user_group_ids | Requirement doc | HARD.md R003 | API-key accounts need group membership for RBAC WHERE clause | 2026-03-23 |
| AC3: audit_logs FK migration | Requirement doc | CONSTITUTION.md C008 | Audit log requires real user_id, not TEXT placeholder | 2026-03-23 |
| AC3: sentinel user strategy | Existing behavior | `backend/db/migrations/001_create_core_schema.sql` | Comment in migration 001: "user_id TEXT placeholder; FK added by auth-agent" | 2026-03-23 |
| AC4: migration file naming | Requirement doc | CONSTITUTION.md C010 | All schema changes via numbered migration files | 2026-03-23 |
| AC4: rollback section | Requirement doc | ARCH.md A006 | Each migration must have rollback section commented at bottom | 2026-03-23 |
| AC5: ORM after migration | Requirement doc | CONSTITUTION.md C010 | ORM models updated AFTER migration file is created and reviewed | 2026-03-23 |
| AC5: __init__.py exports | Existing behavior | `backend/db/models/__init__.py` | Export convention established in db-schema-embeddings (session 2026-03-18) | 2026-03-23 |

### Story S002: API-key authentication middleware

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: verify_api_key signature | Requirement doc | HARD.md R003 | All /v1/* require `Depends(verify_token)` — verify_api_key is the API-key implementation | 2026-03-23 |
| AC1: SHA-256 hash lookup | Requirement doc | SECURITY.md S005 | No plaintext key storage — hash comparison only | 2026-03-23 |
| AC2: AUTH_MISSING error shape | Requirement doc | ARCH.md A005 | Error response: `{"error": {"code": "...", "message": "...", "request_id": "..."}}` | 2026-03-23 |
| AC2: 401 on missing header | Requirement doc | HARD.md R003 + CONSTITUTION.md C003 | No anonymous access to /v1/* | 2026-03-23 |
| AC3: AUTH_INVALID_KEY, no stack trace | Requirement doc | ARCH.md A005 + SECURITY.md S001 | Structured errors; no internal paths exposed in production responses | 2026-03-23 |
| AC4: last_used_at update | Business logic | Q&A 2026-03-23 | Key usage audit for service account monitoring and security review | 2026-03-23 |
| AC5: no rag/api imports | Requirement doc | ARCH.md A001 + A002 | auth-agent scope isolation; dependency direction: api → auth → db only | 2026-03-23 |

### Story S003: OIDC/JWT Bearer authentication middleware

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: JWT validation (sig+exp+iss+aud) | Requirement doc | SECURITY.md S002 | Verify: signature, expiry, issuer, audience on EVERY request | 2026-03-23 |
| AC1: groups → user_group_ids DB lookup | Conversation | Q&A 2026-03-23 — D01 | groups claim = group names (strings); Keycloak default; DB lookup required | 2026-03-23 |
| AC1: JIT UPSERT to users | Conversation | Q&A 2026-03-23 — D02 | JIT provisioning: auto UPSERT on first OIDC login; no IT admin intervention needed | 2026-03-23 |
| AC2: JWKS TTL cache | Requirement doc | SECURITY.md S002 | "Cache public keys with TTL, not forever" — in-process cache with configurable TTL | 2026-03-23 |
| AC2: JWKS_URI env var | Requirement doc | SECURITY.md S005 | All config via env vars; OIDC_JWKS_URI must not be hardcoded | 2026-03-23 |
| AC3: AUTH_MISSING on missing header | Requirement doc | ARCH.md A005 + HARD.md R003 | Consistent error shape; no anonymous access | 2026-03-23 |
| AC4: AUTH_TOKEN_INVALID, no token content | Requirement doc | ARCH.md A005 + SECURITY.md S002 | No stack traces; all 4 JWT claims validated — any failure = 401 | 2026-03-23 |
| AC5: env vars, RuntimeError on missing | Requirement doc | SECURITY.md S005 | Zero hardcoded secrets; fail fast if misconfigured | 2026-03-23 |
| AC5: no hardcoded secrets | Requirement doc | CONSTITUTION.md Non-Negotiables | "Zero hardcoded secrets in source code" — non-overridable constraint | 2026-03-23 |

### Story S004: Unified `verify_token` FastAPI dependency

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: AuthenticatedUser frozen dataclass | Requirement doc | HARD.md R003 + ARCH.md A001 | verify_token must return unified identity; interface defined in auth scope | 2026-03-23 |
| AC2: dispatch logic | Requirement doc | HARD.md R003 + CONSTITUTION.md C003 | Single Depends(verify_token) on all routes; no anonymous access | 2026-03-23 |
| AC3: X-API-Key precedence | Business logic | Q&A 2026-03-23 | API-key precedence when both headers present; bot tokens are more specific identity | 2026-03-23 |
| AC4: error codes + A005 shape | Requirement doc | ARCH.md A005 + CONSTITUTION.md P005 | Exact error shape required; fail fast, fail visibly across languages/timezones | 2026-03-23 |
| AC5: __init__.py public interface | Requirement doc | ARCH.md A001 + A002 | Auth module exports only verify_token + AuthenticatedUser; api-agent never imports internals | 2026-03-23 |

---

## Summary

**Total ACs:** 20
**Fully traced:** 20/20 ✓
**Pending sources:** 0

---

## How to Update

When spec changes or new ACs discovered:
1. Add row to relevant Story table
2. Include source type + reference (must be findable)
3. Add date
4. Update Summary section
5. Commit with message: `docs: update sources traceability for auth-api-key-oidc`

---

## Source Type Reference

| Type | Examples |
|------|----------|
| **Requirement doc** | CONSTITUTION.md, HARD.md, SECURITY.md, ARCH.md |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current migration files, ORM models, established patterns |
| **Business logic** | BrSE analysis, design Q&A decisions |
| **Conversation** | Design Q&A, /specify session decisions (recorded in WARM memory) |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |

---
