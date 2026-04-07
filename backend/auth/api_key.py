# Spec: docs/specs/auth-api-key-oidc.spec.md#S002
# Task: T002 — verify_api_key implementation
# Decision: D05 — X-API-Key takes precedence when both headers present
# Decision: D09 — API key creation = manual SQL seed (no endpoint yet)
import hashlib
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from fastapi import Request

from backend.db.models.api_key import ApiKey
from backend.db.models.user import User

from ._errors import auth_error
from .types import AuthenticatedUser


async def verify_api_key(request: "Request", db: AsyncSession) -> AuthenticatedUser:
    """Extract X-API-Key header, hash it, look up active key, update last_used_at."""
    key = request.headers.get("X-API-Key", "").strip()
    if not key:
        raise auth_error(request, "AUTH_MISSING", "X-API-Key header is required", 401)

    key_hash = hashlib.sha256(key.encode()).hexdigest()

    # Join User to check is_active — ApiKey has no is_active column (S001 schema)
    result = await db.execute(
        select(ApiKey)
        .join(User, ApiKey.user_id == User.id)
        .where(ApiKey.key_hash == key_hash, User.is_active == True)  # noqa: E712
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise auth_error(request, "AUTH_INVALID_KEY", "Invalid or inactive API key", 401)

    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == row.id)
        .values(last_used_at=_now())
    )
    await db.commit()

    return AuthenticatedUser(
        user_id=row.user_id,
        user_group_ids=row.user_group_ids,
        auth_type="api_key",
    )


def _now():
    """Return current UTC datetime as naive — column is TIMESTAMP WITHOUT TIME ZONE."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)
