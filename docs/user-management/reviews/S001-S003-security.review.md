# Code Review: S001 + S003 — Create User + Create API Key
Level: security | Date: 2026-04-21 | Reviewer: Claude Opus

---

## Password Salting Check

### bcrypt.gensalt() — CORRECT

**Code** (`backend/api/routes/admin.py` L424-426):
```python
password_hash: str = _bcrypt_lib.hashpw(
    body.password.encode(), _bcrypt_lib.gensalt(rounds=12)
).decode()
```

**Analysis**:
1. **Unique salt per call**: `bcrypt.gensalt()` calls `os.urandom(16)` internally on every invocation. Each user gets a unique 16-byte cryptographic salt. Two identical passwords produce different hashes.
2. **Salt storage**: bcrypt embeds the salt in the output string (`$2b$12$<22-char-salt><31-char-hash>`). The stored `password_hash` column contains the salt implicitly — no separate "salt" column needed, and this is the standard bcrypt approach.
3. **Cost factor**: rounds=12 means 2^12 = 4096 iterations. This is appropriate for 2026 (industry recommendation is 10-12; OWASP recommends 10+).
4. **No AUTH_SECRET_KEY involvement**: Passwords use bcrypt's own salt mechanism. `AUTH_SECRET_KEY` is NOT used for password hashing — this is correct. Password hashing must be self-contained (bcrypt handles it).
5. **Timing attack mitigation**: The login path (`backend/api/routes/auth.py` L80-86) uses a dummy hash for non-existent users, ensuring constant-time comparison regardless of whether the user exists.

**Verdict**: PASS. No changes required.

---

## API Key Hashing Check

### SHA-256 vs HMAC-SHA-256 — Deep Analysis

**Code** (`backend/api/routes/admin.py` L375-376):
```python
plaintext = "kh_" + secrets.token_hex(16)
key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
```

**Verification** (`backend/auth/api_key.py` L28):
```python
key_hash = hashlib.sha256(key.encode()).hexdigest()
```

#### Entropy analysis
- `secrets.token_hex(16)` = 16 bytes = 128 bits of cryptographic randomness
- Full key = `kh_` + 32 hex chars = 35 chars total
- The entropy is in the random portion: 128 bits
- Brute-force cost at 128 bits: 2^128 operations — computationally infeasible even with leaked DB

#### Plain SHA-256 threat model

| Threat | Risk with plain SHA-256 | Risk with HMAC-SHA-256 |
|--------|------------------------|----------------------|
| DB leak + offline brute-force | Infeasible: 128-bit key space | Infeasible: 128-bit key space + need server secret |
| DB leak + rainbow table | Infeasible: key space too large, `kh_` prefix acts as implicit salt | N/A |
| DB leak + known-key attack | If attacker already has the plaintext key, they don't need the hash | Same — HMAC doesn't help |
| Server secret compromise alone | N/A — no secret involved | Key hashes still safe (attacker needs DB too) |
| DB + server secret compromise | Attacker has hashes, can brute-force (infeasible at 128 bits) | Same outcome — both secrets compromised |

#### HMAC-SHA-256 consideration

The user asks whether `HMAC-SHA256(AUTH_SECRET_KEY, plaintext)` should be used instead of `SHA256(plaintext)`. This is a legitimate defense-in-depth question.

**Arguments FOR HMAC**:
- Adds a second factor: even with full DB dump, attacker needs `AUTH_SECRET_KEY` to verify candidate keys
- Standard practice at GitHub, Stripe, and other API key providers
- Low implementation cost: `hmac.new(secret, plaintext, hashlib.sha256).hexdigest()`

**Arguments AGAINST HMAC (current design is acceptable)**:
- 128-bit entropy makes brute-force infeasible regardless of hashing method
- HMAC adds operational complexity: key rotation requires rehashing all keys
- If `AUTH_SECRET_KEY` is compromised alongside the DB, HMAC provides zero additional protection
- `AUTH_SECRET_KEY` being `None` (OIDC-only deployments) would break API key verification

**Decision**: The current plain SHA-256 implementation is **SECURE** for 128-bit entropy keys. HMAC-SHA-256 is a valid defense-in-depth improvement but NOT a blocker. If the team decides to adopt HMAC, it should use a dedicated `API_KEY_HMAC_SECRET` env var (not `AUTH_SECRET_KEY`, which is for JWT signing) to maintain separation of concerns.

#### Key prefix exposure
- `key_prefix = plaintext[:8]` = `kh_` + first 5 hex chars = 20 bits of key revealed
- Remaining entropy after prefix exposure: 128 - 20 = 108 bits — still computationally infeasible
- Prefix is standard practice for key identification (GitHub `ghp_`, Stripe `sk_live_`)

**Verdict**: PASS. No blocker. Optional improvement noted below.

---

## AUTH_SECRET_KEY Usage Check

### Separation of Concerns — CORRECT

| Component | Uses AUTH_SECRET_KEY? | Purpose |
|-----------|----------------------|---------|
| `backend/api/routes/auth.py` L33-35 | YES | HS256 JWT signing (login token issuance) |
| `backend/auth/dependencies.py` L28, L67-73 | YES | HS256 JWT verification (token decode) |
| `backend/api/routes/admin.py` L424-426 | NO | Password hashing uses bcrypt (self-salted) |
| `backend/api/routes/admin.py` L376 | NO | API key hashing uses plain SHA-256 |
| `backend/auth/api_key.py` L28 | NO | API key verification uses plain SHA-256 |

**Analysis**:
1. `AUTH_SECRET_KEY` is correctly scoped to JWT signing/verification only
2. It is NOT used for password hashing (bcrypt handles its own keying)
3. It is NOT used for API key hashing (SHA-256 is keyless)
4. `backend/api/routes/auth.py` has a `RuntimeError` guard at module level if `AUTH_SECRET_KEY` is missing — fail-fast is correct
5. `backend/auth/dependencies.py` treats `None` as "skip HS256 path" — this supports OIDC-only deployments, which is an intentional design

**Verdict**: PASS. AUTH_SECRET_KEY is correctly isolated to its JWT purpose.

---

## Hard Rules Compliance

### S001 — SQL Injection Prevention
| Location | Query | Method | Status |
|----------|-------|--------|--------|
| admin.py L415 | SELECT users by sub | `text().bindparams(sub=sub)` | PASS |
| admin.py L431-439 | INSERT user | `text().bindparams(sub, email, display_name, password_hash)` | PASS |
| admin.py L450-452 | INSERT membership | `text().bindparams(user_id, group_id)` | PASS |
| admin.py L469-471 | SELECT groups | `text().bindparams(group_ids=list(...))` | PASS |
| admin.py L580-581 | SELECT user exists | `text().bindparams(user_id=user_id)` | PASS |
| admin.py L600-610 | INSERT api_key | `text().bindparams(id, user_id, key_hash, key_prefix, name)` | PASS |
| api_key.py L31-35 | SELECT ApiKey JOIN User | ORM `.where()` clause | PASS |

**No f-string interpolation found anywhere in these paths.** PASS.

### S002 — JWT Validation
- `verify_token` in `dependencies.py` L67-72: validates signature, expiry, required claims (`exp`, `sub`, `user_id`)
- `require_admin` wraps `verify_token` — no bypass possible
- All three endpoints (S001 create user, S002 delete user, S003 create API key) use `dependencies=[Depends(require_admin)]`

PASS.

### S003 — Input Sanitization
- `_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")` strips control characters
- Applied to: `sub` (L406), `display_name` (L408-411), API key `name` (L590-591)
- Pydantic enforces: `sub` pattern `^[a-zA-Z0-9_.@-]+$`, `password` min_length=12, `email` via EmailStr, `name` max_length=100
- `user_id` path parameter validated as `uuid.UUID` by FastAPI

PASS.

### S004 — Rate Limiting
- Login endpoint (`/v1/auth/token`) has rate limiting: 10 req/min per IP
- Admin endpoints (S001, S003) do NOT have explicit rate limiting
- Admin endpoints are protected by `require_admin` — exposure is limited to authenticated admin users only
- Recommendation: Add rate limiting for admin endpoints in a future sprint (non-blocking)

PASS (with note).

### S005 — Secret Management
- No hardcoded secrets in any reviewed file
- `AUTH_SECRET_KEY`: `os.getenv("AUTH_SECRET_KEY")`
- bcrypt salt: generated at runtime via `gensalt()`
- API key: generated at runtime via `secrets.token_hex(16)`

PASS.

---

## Issues Found

### BLOCKERS: 0

### WARNINGS: 2 (non-blocking, optional improvements)

#### W1: Consider HMAC-SHA-256 for API key hashing (defense-in-depth)
- **Severity**: LOW — 128-bit entropy makes this non-critical
- **Current**: `hashlib.sha256(plaintext.encode()).hexdigest()`
- **Alternative**: `hmac.new(os.getenv("API_KEY_HMAC_SECRET").encode(), plaintext.encode(), hashlib.sha256).hexdigest()`
- **Impact**: Adds protection against DB-only compromise (attacker would also need server secret)
- **Trade-off**: Requires new env var `API_KEY_HMAC_SECRET` (NOT `AUTH_SECRET_KEY`), key rotation complexity
- **Action**: Track as future improvement. If adopted, requires migration to rehash existing keys.

#### W2: Missing error handling on API key INSERT commit
- **Severity**: LOW — unlikely to fail after user existence check passes
- **Current**: `admin_generate_api_key` (L599-612) has no try/except around INSERT + commit
- **Contrast**: `admin_create_user` (L429-462) has full try/except with rollback
- **Action**: Add try/except with rollback for consistency

---

## Security Criteria Checklist

| Rule | Scope | Status | Evidence |
|------|-------|--------|----------|
| R003 | Auth on routes | PASS | `require_admin` on L393, L502, L563 |
| R004 | /v1/ prefix | PASS | All routes under `/v1/admin/` |
| S001 | SQL injection | PASS | `text().bindparams()` on all queries |
| S002 | JWT validation | PASS | `verify_token` checks sig + exp + claims |
| S003 | Input sanitization | PASS | Control char strip + Pydantic validation |
| S004 | Rate limiting | NOTE | Admin endpoints rely on auth gate only |
| S005 | Secret management | PASS | All secrets from env; no hardcoded values |

---

## Verdict

[x] APPROVED [ ] CHANGES_REQUIRED [ ] BLOCKED

Blockers: 0
Warnings: 2 (W1: HMAC consideration, W2: missing try/except on API key INSERT)

### Summary

**Password salting**: CORRECT. `bcrypt.gensalt(rounds=12)` generates a unique 16-byte cryptographic salt per call. The salt is embedded in the hash output. No separate salt column or `AUTH_SECRET_KEY` involvement needed.

**API key hashing**: CORRECT. `SHA-256(plaintext)` with 128-bit entropy key is computationally secure. HMAC-SHA-256 is a valid defense-in-depth option but not required given the entropy level. If adopted in the future, use a dedicated `API_KEY_HMAC_SECRET` env var, not `AUTH_SECRET_KEY`.

**AUTH_SECRET_KEY**: CORRECTLY SCOPED. Used only for HS256 JWT signing/verification. Not involved in password hashing (bcrypt) or API key hashing (SHA-256). This is the right separation.

**HMAC verdict**: Not a blocker. Plain SHA-256 is secure at 128-bit entropy. HMAC adds defense-in-depth but introduces operational complexity (key rotation, new env var). Track as optional future improvement.

---

### Post-Review Actions

- S001 security review: PASS
- S003 security review: PASS
- Decision recorded: D-SEC-01 — Plain SHA-256 approved for API key hashing at 128-bit entropy; HMAC-SHA-256 deferred as optional improvement
- W1 (HMAC) tracked as future improvement
- W2 (try/except) tracked for S003 consistency fix
