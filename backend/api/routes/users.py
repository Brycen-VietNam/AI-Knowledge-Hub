# Spec: docs/change-password/spec/change-password.spec.md#S001
# Task: S001/T004 — PATCH /v1/users/me/password (self-service change)
# Rule: R003 — Depends(verify_token) on route
# Rule: R004 — /v1/ prefix
# Rule: R006 — audit log on password change
# Rule: S001 — parameterized SQL only
# Rule: S003 — password length 8–128 (bcrypt DoS guard)
# Rule: A005 — error shape {"error": {"code", "message", "request_id"}}
# Decision: D1 — API-key callers → 403 ERR_API_KEY_NOT_ALLOWED
# Decision: D3 — OIDC users (no password_hash) → 400 ERR_PASSWORD_NOT_APPLICABLE
import logging
import uuid
from typing import Annotated

import bcrypt as _bcrypt_lib
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser

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
    """Self-service password change. Clears must_change_password flag on success.

    Returns 204 No Content on success.
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

    # S001: parameterized SELECT — fetch password_hash to verify current password
    row = (await db.execute(
        text("SELECT password_hash FROM users WHERE id = :user_id AND is_active = TRUE")
        .bindparams(user_id=user.user_id)
    )).fetchone()

    if row is None:
        return JSONResponse(
            status_code=401,
            content=_error(request_id, "AUTH_FAILED", "User not found or inactive"),
        )

    stored_hash: str | None = row[0]

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

    # S001: parameterized UPDATE — no f-string interpolation
    await db.execute(
        text(
            "UPDATE users SET password_hash = :hash, must_change_password = FALSE "
            "WHERE id = :user_id"
        ).bindparams(hash=new_hash, user_id=user.user_id)
    )
    await db.commit()

    # R006: audit log — password_change action (no password value in log)
    _logger.info(
        "password_change user_id=%s request_id=%s",
        user.user_id,
        request_id,
    )

    return Response(status_code=204)
