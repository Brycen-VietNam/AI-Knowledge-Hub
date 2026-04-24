# Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S000
# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Spec: docs/security-audit/spec/security-audit.spec.md#S001
# Task: T002 — POST /v1/auth/token route + bcrypt verify
# Task: S000/T009 — add is_admin to token response (AC14)
# Task: S001/T002 — login response adds refresh_token (additive, C004)
# Task: S001/T003 — new POST /v1/auth/refresh route
# Task: S001/T004 — login SELECT extends to token_version
# Decision: D005 — username/password local auth (bcrypt + HS256 JWT)
# Decision: D008 — this endpoint is public (no verify_token); like /v1/health
# Decision: D010 — AUTH_SECRET_KEY generated and stored in .env (never committed)
# Decision: D011 — token carries exp; SPA does proactive refresh at exp-5min
# Decision: D-SA-01 — JWT_REFRESH_SECRET separate from AUTH_SECRET_KEY
# Decision: D-SA-07 — /v1/auth/refresh is local HS256 only; OIDC tokens → AUTH_UNSUPPORTED
# Rule: R003 — explicitly public: /v1/auth/token, /v1/auth/refresh (different auth dep)
# Rule: R004 — route prefix /v1/
# Rule: S001 — parameterized SQL for user lookup (text().bindparams())
# Rule: S004 — rate limit 10 req/min per IP login; 30/min refresh
# Rule: S005 — secrets from env only; RuntimeError if absent
import datetime
import os
import uuid

import bcrypt as _bcrypt_lib
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from backend.api.middleware.rate_limiter import RateLimiter
from backend.auth._errors import auth_error
from backend.auth.dependencies import _compute_is_admin, get_db
from backend.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_AUTH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))

# S004: 10/min for login; 30/min for refresh (lighter attack surface than login)
_rate_limiter = RateLimiter(resource="auth_login", limit=10, window=60)
_refresh_rate_limiter = RateLimiter(resource="auth_refresh", limit=30, window=60)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter()


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/v1/auth/token")
async def login(
    request: Request,
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Issue HS256 JWT for valid username/password credentials.

    Public endpoint — no verify_token dependency (R003 exception, D008).
    Rate limited: 10 req/min per client IP (S004).
    Uniform 401 AUTH_FAILED for both wrong-password and unknown-user (no enumeration).
    Audit logs AUTH_FAILED events only (no password, no success log).
    """
    # S004: rate limit by client IP (user unknown at login time)
    client_ip = request.client.host if request.client else "unknown"
    valkey_client = getattr(request.app.state, "valkey_client", None)
    if valkey_client is not None:
        allowed, remaining, _ = await _rate_limiter.check(client_ip, valkey_client)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if not allowed:
            raise auth_error(request, "RATE_LIMIT_EXCEEDED", "Too many login attempts", 429)

    # S001: parameterized SQL — no f-string interpolation
    # T004: include token_version in SELECT (4th column); defaults to 1 until S002 migration
    result = await db.execute(
        text(
            "SELECT id, password_hash, must_change_password, token_version FROM users "
            "WHERE sub = :username AND is_active = TRUE"
        ).bindparams(username=form.username)
    )
    row = result.fetchone()

    # Verify password — must run even when row is None to prevent timing attacks.
    # bcrypt.checkpw() is constant-time; dummy hash ensures uniform timing on miss.
    # Dummy is a valid bcrypt hash of "dummy" — required so checkpw() doesn't raise.
    _DUMMY_HASH = b"$2b$12$0GjHRQf39w/lWgQsF0zpv.nhMr0.DFIJNeOvbXcEfdKa4tm/2A4gy"
    stored_hash: str | None = row[1] if row is not None else None
    must_change_password: bool = bool(row[2]) if row is not None and row[2] is not None else False
    token_version: int = int(row[3]) if row is not None and row[3] is not None else 1
    hash_bytes = stored_hash.encode() if stored_hash is not None else _DUMMY_HASH
    password_ok = _bcrypt_lib.checkpw(form.password.encode(), hash_bytes)

    if row is None or stored_hash is None or not password_ok:
        # R006: audit AUTH_FAILED (no password in log)
        import logging
        logging.getLogger(__name__).warning(
            "AUTH_FAILED username=%s ip=%s",
            form.username,
            client_ip,
        )
        raise auth_error(request, "AUTH_FAILED", "Invalid credentials", 401)

    user_id: uuid.UUID = row[0]

    # T002: use jwt module functions (extracted from inline); T004: pass token_version
    access_token = create_access_token(
        sub=form.username,
        user_id=str(user_id),
        token_version=token_version,
    )
    refresh_token = create_refresh_token(sub=form.username, user_id=str(user_id))

    # AC14: compute is_admin from group membership — NOT stored in JWT (recomputed at verify_token)
    is_admin = await _compute_is_admin(user_id, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": _AUTH_TOKEN_EXPIRE_MINUTES * 60,
        "is_admin": is_admin,
        "must_change_password": must_change_password,
    }


@router.post("/v1/auth/refresh")
async def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Issue new access + refresh tokens from a valid refresh token.

    Public endpoint using verify_refresh_token (not verify_token — R003 D-SA-07).
    Rate limited: 30 req/min per client IP (S004).
    OIDC tokens rejected with AUTH_UNSUPPORTED — refresh via IdP (D-SA-07).
    """
    client_ip = request.client.host if request.client else "unknown"
    valkey_client = getattr(request.app.state, "valkey_client", None)
    if valkey_client is not None:
        allowed, remaining, _ = await _refresh_rate_limiter.check(client_ip, valkey_client)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if not allowed:
            raise auth_error(request, "RATE_LIMIT_EXCEEDED", "Too many refresh attempts", 429)

    try:
        payload = verify_refresh_token(body.refresh_token)
    except ValueError:
        # D-SA-07: both expired/tampered tokens and OIDC tokens fail here → same 401
        raise auth_error(request, "AUTH_TOKEN_INVALID", "Invalid or expired refresh token", 401)

    uid = payload.get("user_id")
    sub = payload.get("sub")

    # S001: parameterized lookup; include token_version for access token
    result = await db.execute(
        text(
            "SELECT id, sub, token_version FROM users "
            "WHERE id = :uid AND is_active = TRUE"
        ).bindparams(uid=uid)
    )
    row = result.fetchone()
    if row is None:
        raise auth_error(request, "AUTH_TOKEN_INVALID", "User not found or inactive", 401)

    user_id: uuid.UUID = row[0]
    db_sub: str = row[1]
    token_version: int = int(row[2]) if row[2] is not None else 1

    new_access = create_access_token(sub=db_sub, user_id=str(user_id), token_version=token_version)
    new_refresh = create_refresh_token(sub=db_sub, user_id=str(user_id))

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": _AUTH_TOKEN_EXPIRE_MINUTES * 60,
    }
