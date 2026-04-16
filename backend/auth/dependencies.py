# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Task: T002 — verify_token + get_db FastAPI dependencies
# Task: T004 — dual-mode verify_token: HS256 local JWT + RS256/ES256 OIDC
# Decision: D05 — X-API-Key takes precedence when both headers present
# Decision: T004 — HS256 tried before OIDC; fall through on any jwt error (backward compat)
# Rule: A002 — auth imports from db only (no api/rag); A005 — AUTH_MISSING via _errors.py
# Rule: S001 — parameterized SQL for user lookup; S002 — PyJWT validates exp automatically
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
    if x_api_key:
        return await verify_api_key(request, db)

    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")

        local_user = await _verify_local_jwt(token, db)
        if local_user is not None:
            return local_user

        return await verify_oidc_token(request, token, db)

    raise auth_error(request, "AUTH_MISSING", "Authentication required", 401)
