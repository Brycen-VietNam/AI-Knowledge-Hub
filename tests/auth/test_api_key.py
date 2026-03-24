# Spec: docs/specs/auth-api-key-oidc.spec.md#S002
# Task: T003 — Tests for verify_api_key (TDD)
import sys
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.auth.api_key import verify_api_key

# Import HTTPException from fastapi only for isinstance checks.
# fastapi may not be installed in test-only environments (SQLAlchemy-only venv).
# Fall back to catching the base Exception and duck-typing the attributes.
try:
    from fastapi import HTTPException as _HTTPException
except ImportError:  # pragma: no cover
    _HTTPException = Exception  # type: ignore[assignment,misc]


def _make_request(api_key: str | None = None) -> MagicMock:
    """Build a mock FastAPI Request with optional X-API-Key header."""
    request = MagicMock()
    request.headers = {"X-API-Key": api_key} if api_key is not None else {}
    request.state = MagicMock(spec=[])  # no request_id attribute → fallback UUID
    return request


def _make_db(row=None) -> AsyncMock:
    """Build a mock AsyncSession. execute() returns scalar_one_or_none() = row."""
    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = row
    db.execute.return_value = execute_result
    return db


def _make_api_key_row(user_id: uuid.UUID | None = None, user_group_ids: list[int] | None = None):
    """Build a mock ApiKey ORM row."""
    row = MagicMock()
    row.id = uuid.uuid4()
    row.user_id = user_id or uuid.uuid4()
    row.user_group_ids = user_group_ids if user_group_ids is not None else [1, 2]
    return row


@pytest.mark.asyncio
async def test_missing_header_returns_401_auth_missing():
    request = _make_request(api_key=None)
    db = _make_db()
    with pytest.raises(_HTTPException) as exc_info:
        await verify_api_key(request, db)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_MISSING"


@pytest.mark.asyncio
async def test_empty_header_returns_401_auth_missing():
    request = _make_request(api_key="")
    db = _make_db()
    with pytest.raises(_HTTPException) as exc_info:
        await verify_api_key(request, db)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_MISSING"


@pytest.mark.asyncio
async def test_invalid_hash_returns_401_auth_invalid_key():
    request = _make_request(api_key="unknown-key")
    db = _make_db(row=None)
    with pytest.raises(_HTTPException) as exc_info:
        await verify_api_key(request, db)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_INVALID_KEY"


@pytest.mark.asyncio
async def test_inactive_key_returns_401_auth_invalid_key():
    """is_active=False filtered at DB level (User.is_active join) → no row returned."""
    request = _make_request(api_key="some-key")
    db = _make_db(row=None)  # join with User.is_active=True returns nothing
    with pytest.raises(_HTTPException) as exc_info:
        await verify_api_key(request, db)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_INVALID_KEY"


@pytest.mark.asyncio
async def test_valid_key_returns_authenticated_user():
    uid = uuid.uuid4()
    row = _make_api_key_row(user_id=uid, user_group_ids=[10, 20])
    request = _make_request(api_key="valid-secret-key")
    db = _make_db(row=row)

    result = await verify_api_key(request, db)

    assert result.user_id == uid
    assert result.user_group_ids == [10, 20]
    assert result.auth_type == "api_key"


@pytest.mark.asyncio
async def test_last_used_at_updated_on_success():
    row = _make_api_key_row()
    request = _make_request(api_key="valid-secret-key")
    db = _make_db(row=row)

    await verify_api_key(request, db)

    # db.execute called twice: SELECT and UPDATE
    assert db.execute.call_count == 2
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_error_shape_has_request_id():
    """auth_error() must include request_id in detail (A005 compliance)."""
    request = _make_request(api_key=None)
    db = _make_db()
    with pytest.raises(_HTTPException) as exc_info:
        await verify_api_key(request, db)
    detail = exc_info.value.detail["error"]
    assert "request_id" in detail
    assert detail["request_id"]  # non-empty


def test_no_rag_api_import():
    """A001: backend.auth.api_key must not pull in backend.rag or backend.api."""
    import backend.auth.api_key  # noqa: F401
    banned = [m for m in sys.modules if m.startswith("backend.rag") or m.startswith("backend.api")]
    assert not banned, f"Cross-boundary imports found: {banned}"
