# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Task: T002 — verify_token + get_db FastAPI dependencies
# Decision: D05 — X-API-Key takes precedence when both headers present
# Rule: A002 — auth imports from db only (no api/rag); A005 — AUTH_MISSING via _errors.py
from typing import AsyncGenerator

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import async_session_factory

from ._errors import auth_error
from .api_key import verify_api_key
from .oidc import verify_oidc_token
from .types import AuthenticatedUser


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession from the shared connection pool."""
    async with async_session_factory() as session:
        yield session


async def verify_token(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """Unified auth dependency: API-key takes precedence over Bearer (D05).

    Dispatch:
      X-API-Key present              → verify_api_key
      Authorization: Bearer <token>  → verify_oidc_token
      neither                        → 401 AUTH_MISSING
    """
    if x_api_key:
        return await verify_api_key(request, db)

    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        return await verify_oidc_token(request, token, db)

    raise auth_error(request, "AUTH_MISSING", "Authentication required", 401)
