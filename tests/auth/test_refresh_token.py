# Spec: docs/security-audit/spec/security-audit.spec.md#S001
# Task: T001 — TDD tests for backend/auth/jwt.py
# Decision: D-SA-01 — JWT_REFRESH_SECRET separate from AUTH_SECRET_KEY
# Decision: D-SA-03 — token_version claim 'tv' in access token
import os
import time

# Set env vars BEFORE importing jwt module (RuntimeError on missing secrets)
os.environ.setdefault("AUTH_SECRET_KEY", "test-access-secret-for-unit-tests-32bytes!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-for-unit-tests-32bytes!")
os.environ.setdefault("AUTH_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("AUTH_REFRESH_TOKEN_EXPIRE_HOURS", "8")

import jwt as _pyjwt
import pytest

from backend.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

_ACCESS_SECRET = os.environ["AUTH_SECRET_KEY"]
_REFRESH_SECRET = os.environ["JWT_REFRESH_SECRET"]


class TestCreateAccessToken:
    def test_returns_valid_hs256_jwt(self):
        token = create_access_token("alice", "user-uuid-1")
        payload = _pyjwt.decode(token, _ACCESS_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "alice"
        assert payload["user_id"] == "user-uuid-1"
        assert "exp" in payload
        assert "iat" in payload

    def test_default_token_version_is_1(self):
        token = create_access_token("bob", "user-uuid-2")
        payload = _pyjwt.decode(token, _ACCESS_SECRET, algorithms=["HS256"])
        assert payload["tv"] == 1

    def test_custom_token_version_embedded(self):
        token = create_access_token("carol", "user-uuid-3", token_version=5)
        payload = _pyjwt.decode(token, _ACCESS_SECRET, algorithms=["HS256"])
        assert payload["tv"] == 5

    def test_uses_auth_secret_key_not_refresh_secret(self):
        token = create_access_token("alice", "uid")
        # Must decode with access secret
        _pyjwt.decode(token, _ACCESS_SECRET, algorithms=["HS256"])
        # Must NOT decode with refresh secret
        with pytest.raises(_pyjwt.PyJWTError):
            _pyjwt.decode(token, _REFRESH_SECRET, algorithms=["HS256"])


class TestCreateRefreshToken:
    def test_returns_valid_hs256_jwt(self):
        token = create_refresh_token("alice", "user-uuid-1")
        payload = _pyjwt.decode(token, _REFRESH_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "alice"
        assert payload["user_id"] == "user-uuid-1"
        assert "exp" in payload

    def test_uses_refresh_secret_not_access_secret(self):
        token = create_refresh_token("alice", "uid")
        # Must decode with refresh secret
        _pyjwt.decode(token, _REFRESH_SECRET, algorithms=["HS256"])
        # Must NOT decode with access secret
        with pytest.raises(_pyjwt.PyJWTError):
            _pyjwt.decode(token, _ACCESS_SECRET, algorithms=["HS256"])

    def test_d_sa_01_secrets_are_different(self):
        """D-SA-01: JWT_REFRESH_SECRET must differ from AUTH_SECRET_KEY."""
        assert _ACCESS_SECRET != _REFRESH_SECRET


class TestVerifyRefreshToken:
    def test_valid_token_returns_payload(self):
        token = create_refresh_token("alice", "user-uuid-1")
        payload = verify_refresh_token(token)
        assert payload["sub"] == "alice"
        assert payload["user_id"] == "user-uuid-1"

    def test_expired_token_raises_value_error(self):
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        expired_token = _pyjwt.encode(
            {
                "sub": "alice",
                "user_id": "uid",
                "exp": now - __import__("datetime").timedelta(hours=1),
                "iat": now - __import__("datetime").timedelta(hours=2),
            },
            _REFRESH_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(ValueError):
            verify_refresh_token(expired_token)

    def test_tampered_token_raises_value_error(self):
        token = create_refresh_token("alice", "uid")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(ValueError):
            verify_refresh_token(tampered)

    def test_access_token_rejected_as_refresh_token(self):
        """OIDC / access tokens cannot be used as refresh tokens (D-SA-07)."""
        access_token = create_access_token("alice", "uid")
        with pytest.raises(ValueError):
            verify_refresh_token(access_token)

    def test_missing_required_claim_raises_value_error(self):
        bad_token = _pyjwt.encode(
            {"sub": "alice", "exp": int(time.time()) + 3600},
            _REFRESH_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(ValueError):
            verify_refresh_token(bad_token)
