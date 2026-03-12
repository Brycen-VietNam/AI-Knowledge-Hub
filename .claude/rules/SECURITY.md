# SECURITY RULES
# Auto-checked in /reviewcode --level security

## S001 — SQL Injection
All DB queries via SQLAlchemy text() with named params or ORM. Zero string interpolation.
`text("WHERE id = :id").bindparams(id=user_id)` ✅
`f"WHERE id = {user_id}"` ❌ HARD BLOCK

## S002 — JWT Validation
Verify: signature, expiry, issuer, audience on EVERY request.
Never trust unverified claims. Cache public keys with TTL, not forever.

## S003 — Input Sanitization
Query strings: strip control chars, limit to 512 tokens before embedding.
File uploads: validate MIME type + magic bytes, not just extension.

## S004 — Rate Limiting
/v1/query: 60 req/min per user_id (API-key) or sub claim (OIDC).
/v1/documents: 20 req/min for writes.
Use Redis sliding window or FastAPI middleware.

## S005 — Secret Management
Zero hardcoded secrets. All via environment variables.
`os.getenv("DATABASE_URL")` ✅  |  `DATABASE_URL = "postgres://..."` ❌
CI: run `grep -rn "password\|secret\|api_key" src/ --include="*.py"` as gate.
