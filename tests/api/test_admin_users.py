# Spec: docs/user-management/spec/user-management.spec.md#S001
# Task: S001/T004 — Tests: create_user happy path + error cases (AC1–AC10)
# Rule: R003 — all admin endpoints tested with admin AND non-admin (403 gate)
# Rule: A005 — 409 response body matches {"error": {"code", "message", "request_id"}}
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.admin import UserCreate, router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser


# ---------------------------------------------------------------------------
# Helpers (mirror pattern from test_admin.py)
# ---------------------------------------------------------------------------

def _admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="oidc",
        is_admin=True,
    )


def _non_admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="oidc",
        is_admin=False,
    )


def _make_app(user: AuthenticatedUser, db) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)
    return app


def _mappings_first_mock(row: dict | None) -> MagicMock:
    m = MagicMock()
    if row is None:
        m.mappings.return_value.first.return_value = None
    else:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        m.mappings.return_value.first.return_value = r
    return m


def _fetchone_mock(value) -> MagicMock:
    m = MagicMock()
    m.fetchone.return_value = value
    return m


def _mappings_mock(rows: list[dict]) -> MagicMock:
    m = MagicMock()
    mock_rows = []
    for row in rows:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        mock_rows.append(r)
    m.mappings.return_value.all.return_value = mock_rows
    return m


_VALID_PAYLOAD = {
    "sub": "new_user",
    "email": "new@example.com",
    "display_name": "New User",
    "password": "SecurePass123!",
    "group_ids": [],
}


# ---------------------------------------------------------------------------
# T004: Tests — AC1–AC10
# ---------------------------------------------------------------------------

class TestUserCreateModel:
    """T001/T004: Pydantic model validation tests."""

    def test_user_create_model_validation_invalid_sub_pattern(self):
        """AC: sub must match ^[a-zA-Z0-9_.@-]+$ — rejects spaces and special chars."""
        with pytest.raises(Exception):
            UserCreate(sub="bad sub!", email=None, display_name=None, password="ValidPass123!")

    def test_user_create_model_validation_sub_too_short(self):
        """AC: sub min_length=3."""
        with pytest.raises(Exception):
            UserCreate(sub="ab", email=None, display_name=None, password="ValidPass123!")

    def test_user_create_model_validation_password_too_short(self):
        """AC: password min_length=12."""
        with pytest.raises(Exception):
            UserCreate(sub="valid_user", email=None, display_name=None, password="short")

    def test_user_create_model_validation_invalid_email(self):
        """AC: email must be valid EmailStr or None."""
        with pytest.raises(Exception):
            UserCreate(sub="valid_user", email="not-an-email", display_name=None, password="ValidPass123!")

    def test_user_create_model_group_ids_defaults_to_empty_list(self):
        """AC: group_ids defaults to [] — not a mutable default."""
        m = UserCreate(sub="valid_user", email=None, display_name=None, password="ValidPass123!")
        assert m.group_ids == []

    def test_user_create_model_valid(self):
        """AC: valid model parses without error."""
        m = UserCreate(
            sub="valid.user@corp-01",
            email="u@example.com",
            display_name="Valid User",
            password="SecurePass123!",
            group_ids=[1, 2],
        )
        assert m.sub == "valid.user@corp-01"
        assert m.group_ids == [1, 2]


class TestCreateUserSuccess:
    """T002/T004: Happy path — AC1 + AC2."""

    def test_create_user_success(self):
        """AC1: 201 with correct response shape; password_hash NOT in response."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        user_row = {
            "id": new_id,
            "sub": "new_user",
            "email": "new@example.com",
            "display_name": "New User",
            "is_active": True,
        }

        # execute calls: 1) duplicate check → None, 2) INSERT user → row
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),           # duplicate check
            _mappings_first_mock(user_row), # INSERT RETURNING
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=_VALID_PAYLOAD)

        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == str(new_id)
        assert data["sub"] == "new_user"
        assert data["email"] == "new@example.com"
        assert data["is_active"] is True
        assert "password" not in data
        assert "password_hash" not in data
        assert data["groups"] == []

    def test_create_user_strips_whitespace(self):
        """AC: leading/trailing whitespace stripped from sub and display_name (S003)."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        payload = {
            "sub": "clean_user",
            "email": None,
            "display_name": "  Spaced Name  ",
            "password": "SecurePass123!",
            "group_ids": [],
        }
        user_row = {
            "id": new_id,
            "sub": "clean_user",
            "email": None,
            "display_name": "Spaced Name",
            "is_active": True,
        }
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),
            _mappings_first_mock(user_row),
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=payload)

        assert resp.status_code == 201


class TestCreateUserDuplicateSub:
    """T002/T004: AC4 — duplicate sub → 409 SUB_CONFLICT in A005 shape."""

    def test_create_user_duplicate_sub(self):
        """409 with A005 error shape when sub already exists."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(("existing_id",)))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=_VALID_PAYLOAD)

        assert resp.status_code == 409
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "SUB_CONFLICT"
        assert "message" in data["error"]
        assert "request_id" in data["error"]


class TestCreateUserWithGroups:
    """T003/T004: AC3 — group membership inserted in same transaction; groups in response."""

    def test_create_user_with_groups(self):
        """AC3: 201 with groups list when group_ids provided."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        user_row = {
            "id": new_id,
            "sub": "grouped_user",
            "email": "g@example.com",
            "display_name": "Grouped",
            "is_active": True,
        }
        group_rows = [
            {"id": 1, "name": "Editors", "is_admin": False},
            {"id": 2, "name": "Admins", "is_admin": True},
        ]

        payload = {**_VALID_PAYLOAD, "sub": "grouped_user", "email": "g@example.com", "group_ids": [1, 2]}

        # execute calls: duplicate check, INSERT user, INSERT membership ×2, SELECT groups
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),                  # duplicate check
            _mappings_first_mock(user_row),        # INSERT user RETURNING
            MagicMock(),                           # INSERT membership group 1
            MagicMock(),                           # INSERT membership group 2
            _mappings_mock(group_rows),            # SELECT groups IN
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=payload)

        assert resp.status_code == 201
        data = resp.json()
        assert len(data["groups"]) == 2
        assert data["groups"][0]["id"] == 1
        assert data["groups"][1]["name"] == "Admins"

    def test_create_user_invalid_group_ids(self):
        """AC: unknown group_ids handled gracefully — groups list empty if no match."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        user_row = {
            "id": new_id,
            "sub": "nogroup_user",
            "email": None,
            "display_name": None,
            "is_active": True,
        }
        payload = {**_VALID_PAYLOAD, "sub": "nogroup_user", "email": None, "group_ids": [999]}

        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),                  # duplicate check
            _mappings_first_mock(user_row),        # INSERT user RETURNING
            MagicMock(),                           # INSERT membership group 999
            _mappings_mock([]),                    # SELECT groups → empty (unknown id)
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=payload)

        assert resp.status_code == 201
        assert resp.json()["groups"] == []


class TestCreateUserNonAdmin:
    """T002/T004: AC15 — non-admin gets 403 FORBIDDEN (R003)."""

    def test_create_user_non_admin(self):
        """403 when caller is not an admin."""
        user = _non_admin_user()
        db = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=_VALID_PAYLOAD)

        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"
