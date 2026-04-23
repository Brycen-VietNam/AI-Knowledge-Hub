# Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S000
# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T002 — POST /v1/auth/token route + bcrypt verify
# Task: S000/T009 — add is_admin to token response (AC14)
# Decision: D005 — username/password local auth (bcrypt + HS256 JWT)
# Decision: D008 — this endpoint is public (no verify_token); like /v1/health
# Decision: D010 — AUTH_SECRET_KEY generated and stored in .env (never committed)
# Decision: D011 — token carries exp; SPA does proactive refresh at exp-5min
# Rule: R003 — explicitly public: /v1/auth/token (exception, documented here)
# Rule: R004 — route prefix /v1/
# Rule: S001 — parameterized SQL for user lookup (text().bindparams())
# Rule: S004 — rate limit 10 req/min per IP (tighter than query 60 req/min)
# Rule: S005 — AUTH_SECRET_KEY from env only; RuntimeError if absent
import datetime
import os
import uuid

import bcrypt as _bcrypt_lib
import jwt
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from backend.api.middleware.rate_limiter import RateLimiter
from backend.auth._errors import auth_error
from backend.auth.dependencies import _compute_is_admin, get_db

# ---------------------------------------------------------------------------
# Config — S005: all secrets from env; fail fast at startup if missing
# ---------------------------------------------------------------------------
_AUTH_SECRET_KEY: str | None = os.getenv("AUTH_SECRET_KEY")
if not _AUTH_SECRET_KEY:
    raise RuntimeError("Missing required env var: AUTH_SECRET_KEY")

_AUTH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))

# S004: 10 req/min per IP for login endpoint (stricter than query 60 req/min)
_rate_limiter = RateLimiter(resource="auth_login", limit=10, window=60)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter()


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
    # Task: S001/T005 — include must_change_password in SELECT (P004: no second query)
    result = await db.execute(
        text(
            "SELECT id, password_hash, must_change_password FROM users "
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
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(minutes=_AUTH_TOKEN_EXPIRE_MINUTES)

    token = jwt.encode(
        {
            "sub": form.username,
            "user_id": str(user_id),
            "exp": expire,
            "iat": now,
        },
        _AUTH_SECRET_KEY,
        algorithm="HS256",
    )

    # AC14: compute is_admin from group membership — NOT stored in JWT (recomputed at verify_token)
    is_admin = await _compute_is_admin(user_id, db)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": _AUTH_TOKEN_EXPIRE_MINUTES * 60,
        "is_admin": is_admin,
        "must_change_password": must_change_password,
    }
