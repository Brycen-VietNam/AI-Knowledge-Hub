# Spec: docs/change-password/spec/change-password.spec.md#S001
# Spec: docs/security-audit/spec/security-audit.spec.md#S001
# Task: S001/T004 — PATCH /v1/users/me/password (self-service change)
# Task: S001/T007 — bump token_version + return 200 with new tokens (D-SA-08)
# Rule: R003 — Depends(verify_token) on route
# Rule: R004 — /v1/ prefix
# Rule: R006 — audit log on password change
# Rule: S001 — parameterized SQL only (no f-string interpolation)
# Rule: S003 — password length 8–128 (bcrypt DoS guard)
# Rule: A005 — error shape {"error": {"code", "message", "request_id"}}
# Decision: D1 — API-key callers → 403 ERR_API_KEY_NOT_ALLOWED
# Decision: D3 — OIDC users (no password_hash) → 400 ERR_PASSWORD_NOT_APPLICABLE
# Decision: D-SA-08 — self-serve change bumps token_version atomically; returns 200+tokens
import logging
import os
import uuid
from typing import Annotated

import bcrypt as _bcrypt_lib
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_db, verify_token
from backend.auth.jwt import create_access_token, create_refresh_token
from backend.auth.types import AuthenticatedUser

_AUTH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))
_logger = logging.getLogger(__name__)

router = APIRouter()


def _error(request_id: str, code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


@router.patch("/v1/users/me/password", dependencies=[Depends(verify_token)])
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Self-service password change. Bumps token_version. Returns 200 with new tokens.

    Returns 200 OK + new access_token + refresh_token on success (D-SA-08).
    403 ERR_API_KEY_NOT_ALLOWED for service accounts (no self identity).
    400 ERR_PASSWORD_NOT_APPLICABLE for OIDC users (no password_hash).
    401 ERR_WRONG_PASSWORD for incorrect current_password.
    422 if new_password violates 8–128 char rule (handled by Pydantic Field).
    """
    request_id = str(uuid.uuid4())

    # D1: block API-key callers — service accounts have no "self" identity
    if user.auth_type == "api_key":
        return JSONResponse(
            status_code=403,
            content=_error(request_id, "ERR_API_KEY_NOT_ALLOWED",
                           "API-key callers cannot change passwords"),
        )

    # S001: parameterized SELECT — fetch password_hash + sub to verify and re-issue token
    row = (await db.execute(
        text("SELECT password_hash, sub FROM users WHERE id = :user_id AND is_active = TRUE")
        .bindparams(user_id=user.user_id)
    )).fetchone()

    if row is None:
        return JSONResponse(
            status_code=401,
            content=_error(request_id, "AUTH_FAILED", "User not found or inactive"),
        )

    stored_hash: str | None = row[0]
    sub: str = row[1]

    # D3: OIDC users have no password_hash — password change not applicable
    if stored_hash is None:
        return JSONResponse(
            status_code=400,
            content=_error(request_id, "ERR_PASSWORD_NOT_APPLICABLE",
                           "Password change is not available for SSO accounts"),
        )

    # Verify current password (constant-time bcrypt check)
    if not _bcrypt_lib.checkpw(body.current_password.encode(), stored_hash.encode()):
        return JSONResponse(
            status_code=401,
            content=_error(request_id, "ERR_WRONG_PASSWORD", "Current password is incorrect"),
        )

    # Hash new password and clear must_change_password flag
    new_hash: str = _bcrypt_lib.hashpw(
        body.new_password.encode(), _bcrypt_lib.gensalt(rounds=12)
    ).decode()

    # D-SA-08: bump token_version atomically in the same UPDATE; use RETURNING to get new value
    # S001: parameterized UPDATE — no f-string interpolation
    update_result = await db.execute(
        text(
            "UPDATE users SET password_hash = :hash, must_change_password = FALSE, "
            "token_version = token_version + 1 "
            "WHERE id = :user_id RETURNING token_version"
        ).bindparams(hash=new_hash, user_id=user.user_id)
    )
    update_row = update_result.fetchone()
    new_tv: int = int(update_row[0]) if update_row is not None else 1

    await db.commit()

    # R006: audit log — password_change action (no password value in log)
    _logger.info(
        "password_change user_id=%s request_id=%s tv=%s",
        user.user_id,
        request_id,
        new_tv,
    )

    # D-SA-08: issue fresh tokens with incremented token_version — SPA replaces stale tokens
    access_token = create_access_token(sub=sub, user_id=str(user.user_id), token_version=new_tv)
    refresh_token = create_refresh_token(sub=sub, user_id=str(user.user_id))

    return JSONResponse(
        status_code=200,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": _AUTH_TOKEN_EXPIRE_MINUTES * 60,
        },
    )
