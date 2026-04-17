# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T002 — verify_token + get_db FastAPI dependencies
# Task: T004 — dual-mode verify_token: HS256 local JWT + RS256/ES256 OIDC
# Task: S000/T004 — _compute_is_admin helper; dataclasses.replace to avoid FrozenInstanceError
# Decision: D05 — X-API-Key takes precedence when both headers present
# Decision: T004 — HS256 tried before OIDC; fall through on any jwt error (backward compat)
# Rule: A002 — auth imports from db only (no api/rag); A005 — AUTH_MISSING via _errors.py
# Rule: S001 — parameterized SQL for user lookup; S002 — PyJWT validates exp automatically
import dataclasses
import os
import uuid
from typing import AsyncGenerator

import jwt
from fastapi import Depends, Header, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import async_session_factory

from ._errors import auth_error
from .api_key import verify_api_key
from .oidc import verify_oidc_token
from .types import AuthenticatedUser

# S005: soft check — None means HS256 path is silently skipped (OIDC-only deployments)
_LOCAL_SECRET: str | None = os.getenv("AUTH_SECRET_KEY")


async def _compute_is_admin(user_id: uuid.UUID, db: AsyncSession) -> bool:
    """Compute is_admin by checking user_group_memberships → user_groups JOIN.

    # Spec: docs/admin-spa/spec/admin-spa.spec.md#S000/AC3
    # Task: S000/T004 — single point: called for ALL auth paths
    # Rule: S001 — parameterized SQL, no f-string interpolation
    Returns True if user belongs to ≥1 group with is_admin=TRUE, False otherwise.
    """
    result = await db.execute(
        text("""
            SELECT BOOL_OR(ug.is_admin) AS is_admin
            FROM user_group_memberships ugm
            JOIN user_groups ug ON ug.id = ugm.group_id
            WHERE ugm.user_id = :user_id
        """).bindparams(user_id=user_id)
    )
    return result.scalar() or False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession from the shared connection pool."""
    async with async_session_factory() as session:
        yield session


async def _verify_local_jwt(token: str, db: AsyncSession) -> AuthenticatedUser | None:
    """Try to verify token as HS256 local JWT. Returns None on any failure (caller falls through).

    # Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S000
    # Task: T004 — HS256 local JWT path
    # Decision: return None (not raise) so OIDC path is attempted on failure
    # Rule: S001 — parameterized SQL; S002 — PyJWT validates exp automatically
    """
    if not _LOCAL_SECRET:
        return None
    try:
        payload = jwt.decode(
            token,
            _LOCAL_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "sub", "user_id"]},
        )
    except jwt.PyJWTError:
        return None

    user_id_str: str = payload["user_id"]
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    # S001: parameterized SQL — verify user still exists and is active
    result = await db.execute(
        text("SELECT id FROM users WHERE id = :user_id AND is_active = TRUE")
        .bindparams(user_id=user_id)
    )
    row = result.fetchone()
    if row is None:
        return None

    return AuthenticatedUser(
        user_id=user_id,
        user_group_ids=[],  # local JWT carries no group claims; empty = permissive (D06)
        auth_type="oidc",   # Literal["api_key","oidc"] — "local" out of scope (T002 decision)
    )


async def verify_token(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """Unified auth dependency: API-key → HS256 local JWT → OIDC → 401 (D05, T004).

    Dispatch order:
      X-API-Key present              → verify_api_key        (D05 priority)
      Authorization: Bearer <token>  → _verify_local_jwt     (HS256 try; None = fall through)
                                     → verify_oidc_token     (RS256/ES256 fallback)
      neither                        → 401 AUTH_MISSING
    """
    # Dispatch auth path; user is always assigned before is_admin computation
    if x_api_key:
        user = await verify_api_key(request, db)
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        local_user = await _verify_local_jwt(token, db)
        user = local_user if local_user is not None else await verify_oidc_token(request, token, db)
    else:
        raise auth_error(request, "AUTH_MISSING", "Authentication required", 401)

    # S000/AC3: compute is_admin for ALL auth paths at single point
    # NOTE: AuthenticatedUser is frozen=True — must use dataclasses.replace, not mutation
    is_admin = await _compute_is_admin(user.user_id, db)
    return dataclasses.replace(user, is_admin=is_admin)
