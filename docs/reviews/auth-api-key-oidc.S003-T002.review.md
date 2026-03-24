# Code Review: S003-T002 — oidc.py env config + JWKS cache
Feature: auth-api-key-oidc | Level: security | Date: 2026-03-23 | Reviewer: Claude (opus)

---

## Files Reviewed (1)

| File | Task | Action |
|------|------|--------|
| `backend/auth/oidc.py` | T002 | created (partial — config + cache only) |

## Task Review Criteria
- [x] `_REQUIRED = ["OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URI"]` checked at module level — L14-17
- [x] Missing required var → `raise RuntimeError(f"Missing required env var: {_v}")` — L17
- [x] `OIDC_GROUPS_CLAIM` defaults to `"groups"`, `OIDC_EMAIL_CLAIM` to `"email"`, `OIDC_NAME_CLAIM` to `"name"` — L23-25
- [x] `OIDC_JWKS_CACHE_TTL` defaults to `3600` (integer seconds) — L26
- [x] `_get_jwks_key(kid)` refreshes when `kid not in cache` OR TTL expired — L59
- [x] `_refresh_jwks_cache()` uses `httpx.AsyncClient(timeout=2.0)` — 2s timeout enforced — L38
- [x] JWKS parsed with `jwt.algorithms.RSAAlgorithm.from_jwk(key)` per key in `jwks["keys"]` — L49
- [x] Rule satisfied: S005 (zero hardcoded issuer/audience/URI strings)
- [x] Rule satisfied: S002 (JWKS cache with TTL, not forever)

## Full Checks
- [x] Error handling: `resp.raise_for_status()` on httpx call — L40
- [x] No magic numbers — timeout and TTL are labeled constants
- [x] Docstrings on `_refresh_jwks_cache` and `_get_jwks_key`
- [x] No commented-out dead code
- [x] No files outside TOUCH list modified

## Security Checks
- [x] S002: JWKS cache with TTL (default 3600s) — not cached forever
- [x] S005: All config values from env vars — zero hardcoded URLs or secrets
- [x] S001: N/A (no SQL in this file)
- [x] R003: N/A (no routes in this file)

## Issues Found

### ⚠️ WARNING — Minor (non-blocking)

1. **L41**: `resp.json()` called outside `async with` block — works because httpx buffers response, but unconventional.

2. **L47**: `kty` defaults to `"RSA"` when missing. Per RFC 7517, `kty` is REQUIRED — missing `kty` should skip the key, not default. Low risk.

3. **L35-53**: `_refresh_jwks_cache()` has no try/except — exceptions propagate to caller. Acceptable because T003 wraps all in `AUTH_TOKEN_INVALID`.

4. **L56**: `_get_jwks_key` missing return type annotation.

## Verdict
**[x] APPROVED** [ ] CHANGES REQUIRED [ ] BLOCKED

Blockers: 0 | Warnings: 4 (minor) | Tests: 8/8 passed
