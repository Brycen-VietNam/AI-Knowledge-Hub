# Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S000
# Task: T002 — POST /v1/auth/token route + bcrypt verify
# Task: T004 — dual-mode verify_token (HS256 + OIDC)
# Decision: D005 — username/password local auth; D008 — S000 is api-agent prerequisite
# Rule: R003 — /v1/auth/token is explicitly public (no verify_token dependency)
# Rule: R004 — route prefix /v1/
# Rule: S001 — parameterized SQL in user lookup
# Rule: S004 — rate limit 10 req/min per IP (separate from query 60 req/min)
import os
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

# Stub required env vars before importing auth modules
os.environ.setdefault("OIDC_ISSUER", "https://test.example.com")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("OIDC_JWKS_URI", "https://test.example.com/.well-known/jwks.json")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key-for-unit-tests-only-32bytes!!")
os.environ.setdefault("AUTH_TOKEN_EXPIRE_MINUTES", "60")

from backend.api.routes.auth import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser

_TEST_USERNAME = "testuser"
_TEST_CREDENTIAL = "correct-pw"  # test fixture — not a real credential
_WRONG_CREDENTIAL = "wrong-password"  # test fixture — not a real credential
_ANY_CREDENTIAL = "anything"  # test fixture — not a real credential
_SOME_CREDENTIAL = "something"  # test fixture — not a real credential
# Pre-generated bcrypt hash of _TEST_CREDENTIAL — avoids bcrypt version compat issues at import time.
# Regenerate with: python -c "import bcrypt; print(bcrypt.hashpw(b'correct-pw', bcrypt.gensalt()).decode())"
_TEST_HASH = "$2b$12$P.evJEN3BlDemojmDqzi8O8WRQ2hzkztez5gacVXCbVJak3wAFxkK"
_TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_app(db=None) -> FastAPI:
    """Build minimal test app. Always override get_db to avoid real DB connections."""
    app = FastAPI()
    app.include_router(router)
    # Always provide a mock DB — FastAPI resolves dependencies even before validation
    # on some versions, and a real DB connection would fail in unit tests.
    app.dependency_overrides[get_db] = lambda: (db if db is not None else _mock_db_no_user())
    return app


def _mock_db_row(username: str, password_hash: str | None, user_id: uuid.UUID):
    """Return a mock AsyncSession that yields one user row on execute()."""
    row = MagicMock()
    row.__getitem__ = lambda self, i: [user_id, password_hash][i]

    result = MagicMock()
    result.fetchone = MagicMock(return_value=row)

    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


def _mock_db_no_user():
    """Return a mock AsyncSession that yields no user (unknown username)."""
    result = MagicMock()
    result.fetchone = MagicMock(return_value=None)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


# ---------------------------------------------------------------------------
# T002 Tests — POST /v1/auth/token
# ---------------------------------------------------------------------------

class TestLoginEndpoint:
    """Tests for POST /v1/auth/token."""

    def test_login_success_returns_token(self):
        """Valid credentials → 200 with access_token, token_type, expires_in."""
        db = _mock_db_row(_TEST_USERNAME, _TEST_HASH, _TEST_USER_ID)
        app = _make_app(db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/v1/auth/token",
                data={"username": _TEST_USERNAME, "password": _TEST_CREDENTIAL},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert isinstance(body["expires_in"], int)
        assert body["expires_in"] > 0

        # Token must be a valid HS256 JWT with correct claims
        secret = os.environ["AUTH_SECRET_KEY"]
        payload = jwt.decode(body["access_token"], secret, algorithms=["HS256"])
        assert payload["sub"] == _TEST_USERNAME
        assert payload["user_id"] == str(_TEST_USER_ID)
        assert "exp" in payload

    def test_login_wrong_password_returns_401(self):
        """Wrong password → 401 AUTH_FAILED (no enumeration)."""
        db = _mock_db_row(_TEST_USERNAME, _TEST_HASH, _TEST_USER_ID)
        app = _make_app(db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/v1/auth/token",
                data={"username": _TEST_USERNAME, "password": _WRONG_CREDENTIAL},
            )

        assert resp.status_code == 401
        body = resp.json()
        assert body["detail"]["error"]["code"] == "AUTH_FAILED"
        # Must NOT reveal whether username exists
        assert "username" not in body["detail"]["error"]["message"].lower()
        assert "user" not in body["detail"]["error"]["message"].lower()

    def test_login_unknown_user_returns_401(self):
        """Unknown username → 401 AUTH_FAILED (same as wrong password — no enumeration)."""
        app = _make_app()  # default mock returns no user

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/v1/auth/token",
                data={"username": "nobody", "password": _ANY_CREDENTIAL},
            )

        assert resp.status_code == 401
        body = resp.json()
        assert body["detail"]["error"]["code"] == "AUTH_FAILED"

    def test_login_missing_username_returns_422(self):
        """Missing required field → 422 Unprocessable Entity."""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/v1/auth/token",
                data={"password": _SOME_CREDENTIAL},
            )
        assert resp.status_code == 422

    def test_login_missing_password_returns_422(self):
        """Missing password field → 422 Unprocessable Entity."""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/v1/auth/token",
                data={"username": "someone"},
            )
        assert resp.status_code == 422

    def test_login_rate_limited_returns_429(self):
        """Rate limit exceeded → 429 with RATE_LIMIT_EXCEEDED code."""
        app = _make_app()
        # Set a sentinel valkey_client so the rate-limit branch is entered in the route.
        # The actual check() call is patched below — valkey_client is never called directly.
        app.state.valkey_client = object()

        with patch("backend.api.routes.auth._rate_limiter") as mock_rl:
            mock_rl.check = AsyncMock(return_value=(False, 0, int(time.time()) + 60))
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.post(
                    "/v1/auth/token",
                    data={"username": "anyone", "password": _ANY_CREDENTIAL},
                )

        assert resp.status_code == 429
        body = resp.json()
        assert body["detail"]["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_login_user_with_null_password_hash_returns_401(self):
        """OIDC user (password_hash=NULL) trying local login → 401 AUTH_FAILED."""
        db = _mock_db_row(_TEST_USERNAME, None, _TEST_USER_ID)
        app = _make_app(db=db)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/v1/auth/token",
                data={"username": _TEST_USERNAME, "password": _TEST_CREDENTIAL},
            )

        assert resp.status_code == 401
        assert resp.json()["detail"]["error"]["code"] == "AUTH_FAILED"


# ---------------------------------------------------------------------------
# T004 Tests — dual-mode verify_token (HS256 local + OIDC)
# ---------------------------------------------------------------------------

_TEST_SECRET = os.environ["AUTH_SECRET_KEY"]
_TEST_USER_UUID = uuid.UUID("00000000-0000-0000-0000-000000000042")


def _make_local_token(user_id: uuid.UUID, username: str, expired: bool = False) -> str:
    """Issue a test HS256 JWT — same shape as the /v1/auth/token route."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        exp = now - datetime.timedelta(hours=1)
    else:
        exp = now + datetime.timedelta(hours=1)
    return jwt.encode(
        {"sub": username, "user_id": str(user_id), "exp": exp, "iat": now},
        _TEST_SECRET,
        algorithm="HS256",
    )


def _mock_db_user_by_id(user_id: uuid.UUID):
    """Mock DB that returns a user row when looked up by id."""
    row = MagicMock()
    row.__getitem__ = lambda self, i: [user_id][i]

    result = MagicMock()
    result.fetchone = MagicMock(return_value=row)

    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


def _make_protected_app(db=None) -> FastAPI:
    """Minimal app with one protected route that uses verify_token dependency."""
    app = FastAPI()

    from typing import Annotated

    @app.get("/v1/protected")
    async def protected(user: Annotated[AuthenticatedUser, Depends(verify_token)]):
        return {"user_id": str(user.user_id), "auth_type": user.auth_type}

    app.dependency_overrides[get_db] = lambda: (db if db is not None else _mock_db_no_user())
    return app


class TestVerifyTokenDualMode:
    """Tests for T004 — HS256 local JWT path in verify_token."""

    def test_local_jwt_resolves_user(self):
        """Valid HS256 local JWT → verify_token returns AuthenticatedUser."""
        db = _mock_db_user_by_id(_TEST_USER_UUID)
        app = _make_protected_app(db=db)
        token = _make_local_token(_TEST_USER_UUID, _TEST_USERNAME)

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get(
                "/v1/protected",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == str(_TEST_USER_UUID)
        assert body["auth_type"] == "oidc"  # local JWT uses "oidc" auth_type (T002 decision)

    def test_expired_local_jwt_falls_to_oidc_then_401(self):
        """Expired HS256 token → falls through to OIDC path; OIDC also fails → 401."""
        db = _mock_db_user_by_id(_TEST_USER_UUID)
        app = _make_protected_app(db=db)
        token = _make_local_token(_TEST_USER_UUID, _TEST_USERNAME, expired=True)

        # Patch verify_oidc_token to raise 401 — same as real OIDC failure behaviour
        from fastapi import HTTPException
        oidc_401 = HTTPException(status_code=401, detail={"error": {"code": "AUTH_TOKEN_INVALID", "message": "Invalid or expired token", "request_id": "test"}})
        with patch("backend.auth.dependencies.verify_oidc_token",
                   new=AsyncMock(side_effect=oidc_401)) as mock_oidc:
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.get(
                    "/v1/protected",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert resp.status_code == 401
        # OIDC path must have been attempted (expired local token should fall through)
        mock_oidc.assert_called_once()

    def test_api_key_path_unchanged(self):
        """X-API-Key header → API-key path; HS256 logic not invoked."""
        app = _make_protected_app()

        with patch("backend.auth.dependencies.verify_api_key",
                   new=AsyncMock(return_value=AuthenticatedUser(
                       user_id=_TEST_USER_UUID,
                       user_group_ids=[1],
                       auth_type="api_key",
                   ))) as mock_api_key:
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.get(
                    "/v1/protected",
                    headers={"X-API-Key": "test-key"},
                )

        assert resp.status_code == 200
        assert resp.json()["auth_type"] == "api_key"
        mock_api_key.assert_called_once()

    def test_no_auth_header_returns_401(self):
        """No auth header → 401 AUTH_MISSING (existing behavior preserved)."""
        app = _make_protected_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/v1/protected")

        assert resp.status_code == 401
        assert resp.json()["detail"]["error"]["code"] == "AUTH_MISSING"


# ---------------------------------------------------------------------------
# T005 — Integration smoke test (auth router registered in create_app)
# ---------------------------------------------------------------------------

def test_smoke_bad_credentials():
    """POST /v1/auth/token with bad credentials via real create_app() → 401 AUTH_FAILED.

    # Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S000
    # Task: T005 — register auth router + integration gate
    # Rule: A005 — 401 body matches {"detail": {"error": {"code": "AUTH_FAILED", ...}}}
    """
    from backend.api.app import create_app

    app = create_app()
    # Override get_db to avoid real DB connection — mock returns no user row
    app.dependency_overrides[get_db] = lambda: _mock_db_no_user()

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post(
            "/v1/auth/token",
            data={"username": "nonexistent", "password": "wrongpassword"},
        )

    assert resp.status_code == 401
    body = resp.json()
    assert body["detail"]["error"]["code"] == "AUTH_FAILED"
    # A005: no stack traces in response
    assert "traceback" not in str(body).lower()
    assert "exception" not in str(body).lower()
    # Route must be registered — verify via OpenAPI schema
    assert "/v1/auth/token" in app.openapi()["paths"]
