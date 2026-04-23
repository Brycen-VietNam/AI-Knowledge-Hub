---
name: DEFERRED-SEC-002 — JWT session invalidation on password reset
description: After admin resets a user's password, existing JWT sessions remain valid for up to 60 min — fix via token_version column
type: feedback
---

After `POST /v1/admin/users/{id}/password-reset`, the target user's existing JWT is still valid until expiry (~60 min). A compromised or handed-off session stays alive.

**Why:** Adding `token_version INT` to `users` table + embedding version in JWT allows immediate invalidation on password reset. Accepted risk for now with 60-min TTL window (Q4 decision in change-password /clarify). Logged as DEFERRED-SEC-002 in change-password report.

**How to apply:** When starting a security hardening sprint — add `token_version` column (migration), embed in JWT on login, validate on every request in `verify_token`. Files: `backend/db/migrations/NNN_add_token_version.sql`, `backend/db/models/user.py`, `backend/auth/`, `backend/api/routes/admin.py` (increment on reset).
