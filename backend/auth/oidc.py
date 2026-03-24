# Spec: docs/specs/auth-api-key-oidc.spec.md#S003
# Task: T002 — env config + JWKS cache; T003 — verify_oidc_token + JIT UPSERT + groups
# Decision: D01 — groups claim = names → DB lookup; D02 — JIT user provisioning
# Decision: D03 — PyJWT >= 2.8; D06 — empty groups permissive; D07 — configurable claims
# Rule: S001 — no f-string SQL; S002 — JWT fully validated; S005 — no hardcoded secrets
import os
import time
import uuid
from typing import TYPE_CHECKING

import httpx
import jwt
import jwt.algorithms
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from fastapi import Request

from backend.auth.types import AuthenticatedUser
from backend.db.models.user_group import UserGroup

from ._errors import auth_error

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
_REQUIRED = ["OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URI"]
for _v in _REQUIRED:
    if not os.getenv(_v):
        raise RuntimeError(f"Missing required env var: {_v}")

OIDC_ISSUER: str = os.environ["OIDC_ISSUER"]
OIDC_AUDIENCE: str = os.environ["OIDC_AUDIENCE"]
OIDC_JWKS_URI: str = os.environ["OIDC_JWKS_URI"]

OIDC_GROUPS_CLAIM: str = os.getenv("OIDC_GROUPS_CLAIM", "groups")
OIDC_EMAIL_CLAIM: str = os.getenv("OIDC_EMAIL_CLAIM", "email")
OIDC_NAME_CLAIM: str = os.getenv("OIDC_NAME_CLAIM", "name")
OIDC_JWKS_CACHE_TTL: int = int(os.getenv("OIDC_JWKS_CACHE_TTL", "3600"))

# ---------------------------------------------------------------------------
# JWKS cache — keyed by kid, refreshed on miss or TTL expiry
# ---------------------------------------------------------------------------
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0.0


async def _refresh_jwks_cache() -> None:
    """Fetch JWKS from IdP and parse RSA/EC public keys into cache."""
    global _jwks_cache, _jwks_fetched_at
    async with httpx.AsyncClient(timeout=2.0) as client:
        resp = await client.get(OIDC_JWKS_URI)
        resp.raise_for_status()
    jwks = resp.json()
    new_cache: dict = {}
    for key_data in jwks.get("keys", []):
        kid = key_data.get("kid")
        if not kid:
            continue
        kty = key_data.get("kty", "RSA")
        if kty == "RSA":
            new_cache[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        elif kty == "EC":
            new_cache[kid] = jwt.algorithms.ECAlgorithm.from_jwk(key_data)
    _jwks_cache = new_cache
    _jwks_fetched_at = time.monotonic()


async def _get_jwks_key(kid: str):
    """Return public key for *kid*. Refresh cache on miss or TTL expiry."""
    now = time.monotonic()
    if kid not in _jwks_cache or (now - _jwks_fetched_at) >= OIDC_JWKS_CACHE_TTL:
        await _refresh_jwks_cache()
    return _jwks_cache.get(kid)


# ---------------------------------------------------------------------------
# OIDC token verification
# ---------------------------------------------------------------------------

async def verify_oidc_token(
    request: "Request", token: str, db: AsyncSession
) -> AuthenticatedUser:
    """Validate Bearer JWT and return AuthenticatedUser. Raises 401 on any failure.

    Pipeline: decode header → fetch JWKS key → full JWT decode (sig+exp+iss+aud+sub)
    → JIT UPSERT user → resolve group names → return AuthenticatedUser.
    All exceptions caught and re-raised as AUTH_TOKEN_INVALID (no payload leakage, AC4).
    """
    # Spec: docs/specs/auth-api-key-oidc.spec.md#S003
    # Decision: D02 — JIT provisioning; D06 — empty groups permissive
    # Rule: S002 — require exp, iss, aud, sub; S001 — parameterized SQL only
    try:
        # Step 1: decode header to extract kid (unverified — for key lookup only)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Step 2: fetch public key from JWKS cache
        public_key = await _get_jwks_key(kid)
        if public_key is None:
            raise ValueError(f"Unknown kid: {kid}")

        # Step 3: full validation — signature + required claims
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256", "ES256"],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except Exception:
        # Intentionally broad — no token payload in error detail (AC4)
        raise auth_error(request, "AUTH_TOKEN_INVALID", "Invalid or expired token", 401)

    sub: str = payload["sub"]
    email: str | None = payload.get(OIDC_EMAIL_CLAIM)
    display_name: str | None = payload.get(OIDC_NAME_CLAIM)
    group_names: list[str] = payload.get(OIDC_GROUPS_CLAIM) or []  # D06: permissive

    # Step 4: JIT UPSERT — auto-provision user on first login (D02)
    user_id = await _jit_upsert_user(db, sub, email, display_name)

    # Step 5: resolve group names → integer IDs (D01)
    user_group_ids = await _resolve_group_ids(db, group_names)

    return AuthenticatedUser(
        user_id=user_id,
        user_group_ids=user_group_ids,
        auth_type="oidc",
    )


async def _jit_upsert_user(
    db: AsyncSession,
    sub: str,
    email: str | None,
    display_name: str | None,
) -> uuid.UUID:
    """INSERT user on first OIDC login; UPDATE email/display_name on subsequent logins.

    Uses text() with named params — no f-string SQL (S001).
    Returns the user's UUID primary key.
    """
    new_id = uuid.uuid4()
    result = await db.execute(
        text(
            "INSERT INTO users (id, sub, email, display_name) "
            "VALUES (:id, :sub, :email, :display_name) "
            "ON CONFLICT (sub) DO UPDATE "
            "SET email = EXCLUDED.email, display_name = EXCLUDED.display_name "
            "RETURNING id"
        ).bindparams(id=new_id, sub=sub, email=email, display_name=display_name)
    )
    await db.commit()
    row = result.fetchone()
    return row[0]


async def _resolve_group_ids(db: AsyncSession, group_names: list[str]) -> list[int]:
    """Return integer IDs for known group names. Unknown names silently ignored (D01/D06).

    Uses ORM parameterized query — no f-string SQL (S001).
    """
    if not group_names:
        return []
    result = await db.execute(
        select(UserGroup.id).where(UserGroup.name.in_(group_names))
    )
    return [row[0] for row in result.fetchall()]
