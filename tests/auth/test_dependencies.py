# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Task: T004 — Tests for verify_token + AuthenticatedUser (TDD)
# Decision: D05 — X-API-Key takes precedence over Bearer
# Rule: A001 — backend.auth exports only verify_token + AuthenticatedUser
# Rule: A005 — all 401 responses conform to error shape
import uuid
from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

# OIDC env vars set by tests/auth/conftest.py before collection.
from backend.auth.dependencies import get_db, verify_token
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

    # Override get_db — no real DB needed
    app.dependency_overrides[get_db] = lambda: None
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
