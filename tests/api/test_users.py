# Spec: docs/change-password/spec/change-password.spec.md#S001
# Task: S001/T004 — PATCH /v1/users/me/password tests
# Task: S001/T006 — route registration smoke test
import os
import uuid
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("OIDC_ISSUER", "https://test.example.com")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("OIDC_JWKS_URI", "https://test.example.com/.well-known/jwks.json")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key-for-unit-tests-only-32bytes!!")

from backend.api.routes.users import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser

_TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_CURRENT_PW = "correct-pw"  # test fixture
_CURRENT_HASH = bcrypt.hashpw(_CURRENT_PW.encode(), bcrypt.gensalt(rounds=4)).decode()


def _oidc_user() -> AuthenticatedUser:
    return AuthenticatedUser(user_id=_TEST_USER_ID, user_group_ids=[], auth_type="oidc")


def _api_key_user() -> AuthenticatedUser:
    return AuthenticatedUser(user_id=_TEST_USER_ID, user_group_ids=[], auth_type="api_key")


def _mock_db_with_hash(password_hash: str | None):
    """Return a mock db session that yields one row with the given password_hash."""
    row = MagicMock()
    row.__getitem__ = lambda self, i: [password_hash][i]
    result = MagicMock()
    result.fetchone = MagicMock(return_value=row)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    return session


def _mock_db_no_user():
    result = MagicMock()
    result.fetchone = MagicMock(return_value=None)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


def _make_app(user: AuthenticatedUser, db=None) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (db if db is not None else _mock_db_no_user())
    return app


class TestChangePasswordEndpoint:
    def test_success_returns_204(self):
        """Valid current_password + strong new_password → 204 No Content."""
        db = _mock_db_with_hash(_CURRENT_HASH)
        app = _make_app(_oidc_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.patch(
                "/v1/users/me/password",
                json={"current_password": _CURRENT_PW, "new_password": "NewStr0ng!"},
            )

        assert resp.status_code == 204

    def test_wrong_password_returns_401(self):
        """Incorrect current_password → 401 ERR_WRONG_PASSWORD."""
        db = _mock_db_with_hash(_CURRENT_HASH)
        app = _make_app(_oidc_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.patch(
                "/v1/users/me/password",
                json={"current_password": "wrongpass", "new_password": "NewStr0ng!"},
            )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "ERR_WRONG_PASSWORD"

    def test_oidc_user_no_hash_returns_400(self):
        """OIDC user (password_hash IS NULL) → 400 ERR_PASSWORD_NOT_APPLICABLE."""
        db = _mock_db_with_hash(None)
        app = _make_app(_oidc_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.patch(
                "/v1/users/me/password",
                json={"current_password": "anything", "new_password": "NewStr0ng!"},
            )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "ERR_PASSWORD_NOT_APPLICABLE"

    def test_api_key_caller_returns_403(self):
        """API-key caller → 403 ERR_API_KEY_NOT_ALLOWED."""
        db = _mock_db_with_hash(_CURRENT_HASH)
        app = _make_app(_api_key_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.patch(
                "/v1/users/me/password",
                json={"current_password": _CURRENT_PW, "new_password": "NewStr0ng!"},
            )

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "ERR_API_KEY_NOT_ALLOWED"

    def test_short_new_password_returns_422(self):
        """new_password < 8 chars → 422 (Pydantic Field min_length)."""
        db = _mock_db_with_hash(_CURRENT_HASH)
        app = _make_app(_oidc_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.patch(
                "/v1/users/me/password",
                json={"current_password": _CURRENT_PW, "new_password": "short"},
            )

        assert resp.status_code == 422

    def test_too_long_new_password_returns_422(self):
        """new_password > 128 chars → 422 (Pydantic Field max_length)."""
        db = _mock_db_with_hash(_CURRENT_HASH)
        app = _make_app(_oidc_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.patch(
                "/v1/users/me/password",
                json={"current_password": _CURRENT_PW, "new_password": "x" * 129},
            )

        assert resp.status_code == 422


class TestRouteRegistered:
    def test_route_registered(self):
        """PATCH /v1/users/me/password appears in openapi schema."""
        db = _mock_db_no_user()
        app = _make_app(_oidc_user(), db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            schema = client.get("/openapi.json").json()

        paths = schema.get("paths", {})
        assert "/v1/users/me/password" in paths
        assert "patch" in paths["/v1/users/me/password"]
