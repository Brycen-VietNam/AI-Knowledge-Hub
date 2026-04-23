# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T004 — Tests for verify_token + AuthenticatedUser (TDD)
# Task: S000/T012 — tests for _compute_is_admin + verify_token is_admin injection (AC2, AC3)
# Decision: D05 — X-API-Key takes precedence over Bearer
# Rule: A001 — backend.auth exports only verify_token + AuthenticatedUser
# Rule: A005 — all 401 responses conform to error shape
import uuid
from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

# OIDC env vars set by tests/auth/conftest.py before collection.
from backend.auth.dependencies import _compute_is_admin, get_db, verify_token
from backend.auth.jwt import create_access_token
from backend.auth.types import AuthenticatedUser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STUB_API_KEY_USER = AuthenticatedUser(
    user_id=uuid.uuid4(),
    user_group_ids=[1, 2],
    auth_type="api_key",
)

_STUB_OIDC_USER = AuthenticatedUser(
    user_id=uuid.uuid4(),
    user_group_ids=[3],
    auth_type="oidc",
)


def _make_app() -> FastAPI:
    """Minimal inline FastAPI app with verify_token dependency."""
    app = FastAPI()

    @app.get("/protected")
    async def protected(user: AuthenticatedUser = Depends(verify_token)):
        return {
            "user_id": str(user.user_id),
            "auth_type": user.auth_type,
        }

    # Mock db: returns is_admin=False for _compute_is_admin (no real DB needed)
    _mock_db = AsyncMock()
    _scalar_result = MagicMock()
    _scalar_result.scalar.return_value = False
    _mock_db.execute = AsyncMock(return_value=_scalar_result)
    app.dependency_overrides[get_db] = lambda: _mock_db
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestVerifyToken:
    def setup_method(self):
        self.app = _make_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_api_key_header_takes_precedence_over_bearer(self):
        """Both headers present → API-key wins (D05)."""
        with patch(
            "backend.auth.dependencies.verify_api_key",
            new=AsyncMock(return_value=_STUB_API_KEY_USER),
        ), patch(
            "backend.auth.dependencies.verify_oidc_token",
            new=AsyncMock(return_value=_STUB_OIDC_USER),
        ):
            resp = self.client.get(
                "/protected",
                headers={"X-API-Key": "key123", "Authorization": "Bearer token456"},
            )
        assert resp.status_code == 200
        assert resp.json()["auth_type"] == "api_key"

    def test_bearer_only_dispatches_to_oidc(self):
        """Only Authorization: Bearer → OIDC path."""
        with patch(
            "backend.auth.dependencies.verify_oidc_token",
            new=AsyncMock(return_value=_STUB_OIDC_USER),
        ):
            resp = self.client.get(
                "/protected",
                headers={"Authorization": "Bearer token456"},
            )
        assert resp.status_code == 200
        assert resp.json()["auth_type"] == "oidc"

    def test_api_key_only_dispatches_to_api_key(self):
        """Only X-API-Key → API-key path."""
        with patch(
            "backend.auth.dependencies.verify_api_key",
            new=AsyncMock(return_value=_STUB_API_KEY_USER),
        ):
            resp = self.client.get(
                "/protected",
                headers={"X-API-Key": "key123"},
            )
        assert resp.status_code == 200
        assert resp.json()["auth_type"] == "api_key"

    def test_no_headers_returns_401_auth_missing(self):
        """Neither header → 401 with AUTH_MISSING code."""
        resp = self.client.get("/protected")
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert detail["error"]["code"] == "AUTH_MISSING"

    def test_all_401_responses_conform_a005_shape(self):
        """401 detail must have error.code, error.message, error.request_id (A005)."""
        resp = self.client.get("/protected")
        assert resp.status_code == 401
        error = resp.json()["detail"]["error"]
        assert "code" in error
        assert "message" in error
        assert "request_id" in error


class TestAuthenticatedUser:
    def test_authenticated_user_is_frozen(self):
        """Mutation attempt raises FrozenInstanceError (AC1)."""
        user = AuthenticatedUser(
            user_id=uuid.uuid4(),
            user_group_ids=[1],
            auth_type="api_key",
        )
        with pytest.raises(FrozenInstanceError):
            user.user_id = uuid.uuid4()  # type: ignore[misc]

    def test_authenticated_user_field_types(self):
        """user_id is UUID, user_group_ids is list, auth_type is str."""
        user = AuthenticatedUser(
            user_id=uuid.uuid4(),
            user_group_ids=[1, 2, 3],
            auth_type="oidc",
        )
        assert isinstance(user.user_id, uuid.UUID)
        assert isinstance(user.user_group_ids, list)
        assert isinstance(user.auth_type, str)


class TestAuthModuleInterface:
    def test_auth_module_not_exporting_internal_functions(self):
        """Internal functions must not be importable from backend.auth (A001/AC5)."""
        import backend.auth as auth_pkg

        for name in ("verify_api_key", "verify_oidc_token", "auth_error"):
            assert not hasattr(auth_pkg, name), (
                f"backend.auth should not export '{name}'"
            )


# ---------------------------------------------------------------------------
# S000/T012: _compute_is_admin + verify_token is_admin injection (AC2, AC3)
# ---------------------------------------------------------------------------

class TestComputeIsAdmin:
    """Tests for _compute_is_admin helper (S000/AC3)."""

    @pytest.mark.asyncio
    async def test_returns_true_when_user_in_admin_group(self):
        """AC3: is_admin=True when user belongs to a group with is_admin=TRUE."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar.return_value = True
        db.execute = AsyncMock(return_value=result)

        user_id = uuid.uuid4()
        is_admin = await _compute_is_admin(user_id, db)
        assert is_admin is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_admin_groups(self):
        """AC3: is_admin=False when user has no admin group memberships."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar.return_value = False
        db.execute = AsyncMock(return_value=result)

        is_admin = await _compute_is_admin(uuid.uuid4(), db)
        assert is_admin is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_memberships(self):
        """AC3: BOOL_OR returns NULL (no rows) → is_admin=False."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar.return_value = None  # BOOL_OR on empty set returns NULL
        db.execute = AsyncMock(return_value=result)

        is_admin = await _compute_is_admin(uuid.uuid4(), db)
        assert is_admin is False


class TestVerifyTokenIsAdmin:
    """Tests for verify_token injecting is_admin=True via dataclasses.replace (AC2)."""

    def test_verify_token_injects_is_admin_true(self):
        """AC2: verify_token returns AuthenticatedUser with is_admin=True from admin group."""
        admin_stub = AuthenticatedUser(
            user_id=uuid.uuid4(),
            user_group_ids=[1],
            auth_type="api_key",
            is_admin=False,  # starts False; verify_token recomputes
        )
        app = FastAPI()

        @app.get("/check")
        async def check(user: AuthenticatedUser = Depends(verify_token)):
            return {"is_admin": user.is_admin}

        mock_db = AsyncMock()
        admin_result = MagicMock()
        admin_result.scalar.return_value = True  # DB says is_admin=True
        mock_db.execute = AsyncMock(return_value=admin_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("backend.auth.dependencies.verify_api_key", new=AsyncMock(return_value=admin_stub)):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/check", headers={"X-API-Key": "any-key"})

        assert resp.status_code == 200
        assert resp.json()["is_admin"] is True

    def test_verify_token_injects_is_admin_false_for_non_admin(self):
        """AC2: verify_token returns is_admin=False when user is not in admin group."""
        stub = AuthenticatedUser(
            user_id=uuid.uuid4(),
            user_group_ids=[1],
            auth_type="api_key",
        )
        app = FastAPI()

        @app.get("/check")
        async def check(user: AuthenticatedUser = Depends(verify_token)):
            return {"is_admin": user.is_admin}

        mock_db = AsyncMock()
        no_admin_result = MagicMock()
        no_admin_result.scalar.return_value = False
        mock_db.execute = AsyncMock(return_value=no_admin_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("backend.auth.dependencies.verify_api_key", new=AsyncMock(return_value=stub)):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/check", headers={"X-API-Key": "any-key"})

        assert resp.status_code == 200
        assert resp.json()["is_admin"] is False


# ---------------------------------------------------------------------------
# S002/T003: _verify_local_jwt tv claim validation
# Spec: docs/security-audit/spec/security-audit.spec.md#S002
# Task: S002/T003
# ---------------------------------------------------------------------------

def _mock_db_with_tv(user_id: uuid.UUID, db_tv: int) -> AsyncMock:
    """Mock DB: first execute → (id, token_version) row; second execute → is_admin scalar."""
    select_row = MagicMock()
    select_row.__getitem__ = lambda self, i: [user_id, db_tv][i]
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=select_row)

    admin_result = MagicMock()
    admin_result.scalar = MagicMock(return_value=False)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[select_result, admin_result])
    return db


def _mock_db_inactive_user() -> AsyncMock:
    """Mock DB: first execute → None (inactive user)."""
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=select_result)
    return db


def _make_app_local_jwt(db) -> FastAPI:
    """FastAPI app that overrides get_db with provided mock (no API-key mock)."""
    app = FastAPI()

    @app.get("/protected")
    async def protected(user: AuthenticatedUser = Depends(verify_token)):
        return {"user_id": str(user.user_id), "auth_type": user.auth_type}

    app.dependency_overrides[get_db] = lambda: db
    return app


class TestVerifyTokenTvClaim:
    """S002/T003: token_version (tv) claim validation in _verify_local_jwt."""

    def test_tv_match_passes(self):
        """jwt_tv=1, db_tv=1 → 200 (matching tv)."""
        user_id = uuid.uuid4()
        token = create_access_token(sub="user|1", user_id=str(user_id), token_version=1)
        db = _mock_db_with_tv(user_id, db_tv=1)

        app = _make_app_local_jwt(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        assert resp.json()["user_id"] == str(user_id)

    def test_tv_stale_returns_401(self):
        """jwt_tv=1, db_tv=2 → 401 ERR_TOKEN_INVALIDATED (token invalidated after admin reset)."""
        user_id = uuid.uuid4()
        token = create_access_token(sub="user|1", user_id=str(user_id), token_version=1)
        db = _mock_db_with_tv(user_id, db_tv=2)

        app = _make_app_local_jwt(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401
        error = resp.json()["detail"]["error"]
        assert error["code"] == "ERR_TOKEN_INVALIDATED"
        assert "request_id" in error

    def test_tv_missing_claim_defaults_to_1(self):
        """No 'tv' in token payload → defaults to tv=1 → passes if db_tv=1 (pre-S001 tokens safe)."""
        user_id = uuid.uuid4()
        # create_access_token always embeds 'tv'; patch to simulate pre-S001 token without 'tv'
        import jwt as _pyjwt
        import datetime
        import os
        secret = os.getenv("AUTH_SECRET_KEY", "test-secret")
        now = datetime.datetime.now(datetime.timezone.utc)
        token = _pyjwt.encode(
            {"sub": "user|1", "user_id": str(user_id), "exp": now + datetime.timedelta(hours=1), "iat": now},
            secret,
            algorithm="HS256",
        )
        db = _mock_db_with_tv(user_id, db_tv=1)

        app = _make_app_local_jwt(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200

    def test_inactive_user_returns_oidc_fallthrough(self):
        """inactive user → row=None → _verify_local_jwt returns None → OIDC fallthrough → 401."""
        from fastapi import HTTPException as _HTTPException
        user_id = uuid.uuid4()
        token = create_access_token(sub="user|1", user_id=str(user_id), token_version=1)
        db = _mock_db_inactive_user()

        # OIDC path also rejects (not a valid OIDC token) → 401
        app = _make_app_local_jwt(db)
        client = TestClient(app, raise_server_exceptions=False)

        oidc_401 = _HTTPException(status_code=401, detail={"error": {"code": "AUTH_FAILED", "message": "x", "request_id": ""}})
        with patch("backend.auth.dependencies.verify_oidc_token", new=AsyncMock(side_effect=oidc_401)):
            resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401
