# Sources Traceability: change-password
Created: 2026-04-22 | Feature spec: `docs/change-password/spec/change-password.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).

---

## AC-to-Source Mapping

### Story S001: Backend — PATCH /v1/users/me/password

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: API-key rejected 403 | Business logic | CONSTITUTION.md C003 | All /v1/* require auth; bots have no "self" identity | 2026-04-22 |
| AC2: body fields | Business logic | Standard password-change pattern | current + new required to prevent session hijack | 2026-04-22 |
| AC3: bcrypt verify | Existing behavior | backend/auth/ + user-management S001 | bcrypt (passlib) already in codebase | 2026-04-22 |
| AC4: 8-char minimum | Business logic | NIST 800-63B baseline | Industry-standard minimum | 2026-04-22 |
| AC5: 204 on success | Business logic | REST convention | No body → 204 No Content | 2026-04-22 |
| AC6: OIDC 400 | Existing behavior | user-management spec OIDC note | password_hash IS NULL for SSO users | 2026-04-22 |
| AC7: verify_token | HARD.md R003 | Auth on every endpoint | Mandatory for all /v1/* routes | 2026-04-22 |
| AC8: audit log | HARD.md R006 | Audit log requirement | Extended to auth mutation events | 2026-04-22 |

### Story S002: Backend — POST /v1/admin/users/{id}/password-reset

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: require_admin | Existing behavior | user-management S003/S004 | Same admin guard pattern | 2026-04-22 |
| AC2: body options | Business logic | Admin unlock/onboard workflow | Admin may not know user's current password | 2026-04-22 |
| AC3: generate one-time | Existing behavior | user-management S001 D2 | Plaintext shown once — established pattern | 2026-04-22 |
| AC4: 204 explicit | Business logic | REST convention | No body → 204 | 2026-04-22 |
| AC5: generate ≥ 16 chars | Business logic | Security — generated > manual minimum | Auto-gen should be stronger than hand-typed | 2026-04-22 |
| AC6: 404 not found | Business logic | Standard CRUD | User missing → 404 ERR_USER_NOT_FOUND | 2026-04-22 |
| AC7: OIDC 400 | Existing behavior | user-management OIDC note | NULL password_hash — can't reset | 2026-04-22 |
| AC8: audit log | HARD.md R006 | Admin acting on another user = high-risk event | Audit required | 2026-04-22 |
| AC9: route standards | HARD.md R003, R004; ARCH.md A005 | Auth, prefix, error shape | Non-negotiable rules | 2026-04-22 |

### Story S003: Frontend — ChangePasswordModal

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: hidden for OIDC | Business logic | UX — hide irrelevant option | OIDC users cannot use password change | 2026-04-22 |
| AC2: three fields | Business logic | Standard UX pattern | current / new / confirm | 2026-04-22 |
| AC3: match validation | Business logic | Client-side guard | Prevent mismatch before API call | 2026-04-22 |
| AC4: 8-char UI validation | Business logic | Mirror S001 AC4 | Consistent validation layer | 2026-04-22 |
| AC5: toast + close | Business logic | SPA standard | Feedback without reload | 2026-04-22 |
| AC6: ERR_WRONG_PASSWORD display | Existing behavior | S001 error codes | Map to user-friendly message | 2026-04-22 |
| AC7: hide for OIDC | Existing behavior | S001 AC6 OIDC path | Consistent with backend response | 2026-04-22 |
| AC8: loading state | Business logic | Prevent double-submit | Standard UX | 2026-04-22 |
| AC9: i18n strings | CONSTITUTION.md | Multilingual principle P003 + Language in Code | All strings via i18n layer | 2026-04-22 |

### Story S004: Frontend — Admin Reset Password in UsersTab

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Reset Password button | Business logic | Per-row admin action | Follows existing delete-row pattern | 2026-04-22 |
| AC2: modal with options | Business logic | Mirror S002 API — manual or generate | Admin workflow | 2026-04-22 |
| AC3: copyable one-time display | Existing behavior | user-management ApiKeyPanel | Copy-to-clipboard pattern exists | 2026-04-22 |
| AC4: 8-char validation | Business logic | Mirror S002 AC5 | Consistent validation | 2026-04-22 |
| AC5: toast + no reload | Business logic | SPA pattern | Consistent with other admin actions | 2026-04-22 |
| AC6: hide for OIDC | Business logic | Mirror S003 AC1 | Only show for password-based users | 2026-04-22 |
| AC7: i18n | CONSTITUTION.md | Multilingual principle P003 | All strings via i18n | 2026-04-22 |
| AC8: loading state | Business logic | Prevent double-submit | Standard UX | 2026-04-22 |

---

### Story S005: Frontend — Force-Change Password Gate

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: check must_change_password | Business logic | S001 AC9 + S002 AC8 | Backend controls flag; frontend reads after login | 2026-04-22 |
| AC2: redirect to /change-password | Business logic | Security requirement | Must change before accessing platform | 2026-04-22 |
| AC3: block all other routes | Business logic | Security requirement | Route guard prevents direct URL bypass | 2026-04-22 |
| AC4: omit current-password field | Business logic | UX — user doesn't know admin-set password | Force-gate context differs from self-service | 2026-04-22 |
| AC5: redirect home on success | Business logic | S001 AC5 clears flag | Gate lifts when PATCH succeeds | 2026-04-22 |
| AC6: no cancel/skip | Business logic | Security requirement | Force is mandatory; no dismiss path | 2026-04-22 |
| AC7: i18n | CONSTITUTION.md | Multilingual principle P003 | All strings via i18n | 2026-04-22 |
| AC8: OIDC skip | Business logic | S001 AC9 — OIDC never has flag set | OIDC users never see this page | 2026-04-22 |

---

## Summary

**Total ACs:** 42
**Fully traced:** 42/42 ✓
**Pending sources:** 0

---

## Open Questions (for /clarify)

1. Does the user list API (`GET /v1/admin/users`) already return `has_password: bool`? If not, S002/S004 need a schema addition.
2. Does the user pill/profile menu exist in the current header? (Assumption in S003 — confirm before /plan)
3. Should password change trigger active session invalidation (force logout on other devices)?
4. Force-change gate: should "current password" field be omitted entirely, or should it be pre-filled and hidden?
5. Does the login response already return `must_change_password`, or does a separate `GET /v1/users/me` call need to be added to the login flow?
