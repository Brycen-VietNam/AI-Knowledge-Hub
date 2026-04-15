# Spec: docs/specs/auth-api-key-oidc.spec.md#S003
# Task: T004 — Tests for verify_oidc_token (TDD)
# Decision: D01 — groups=names; D02 — JIT; D06 — empty groups permissive
import importlib
import os
import sys
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# ---------------------------------------------------------------------------
# RSA key pair — generated once per module for speed
# ---------------------------------------------------------------------------
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()

_KID = "test-key-001"
_ISSUER = "https://keycloak.test/realms/brysen"
_AUDIENCE = "knowledge-hub"
_JWKS_URI = "https://keycloak.test/realms/brysen/protocol/openid-connect/certs"

_OIDC_ENV = {
    "OIDC_ISSUER": _ISSUER,
    "OIDC_AUDIENCE": _AUDIENCE,
    "OIDC_JWKS_URI": _JWKS_URI,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(
    sub: str = "user-sub-001",
    iss: str = _ISSUER,
    aud: str = _AUDIENCE,
    groups: list | None = None,
    exp_offset: int = 3600,
    kid: str = _KID,
    private_key=None,
    omit_claims: list | None = None,
) -> str:
    """Sign a JWT with the test RSA private key."""
    now = int(time.time())
    payload: dict = {
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "exp": now + exp_offset,
        "iat": now,
        "email": "user@brysen.test",
        "name": "Test User",
    }
    if groups is not None:
        payload["groups"] = groups
    for claim in (omit_claims or []):
        payload.pop(claim, None)
    key = private_key or _PRIVATE_KEY
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": kid})


def _make_request() -> MagicMock:
    req = MagicMock()
    req.state = MagicMock(spec=[])
    return req


def _make_db(upsert_user_id: uuid.UUID | None = None, group_ids: list | None = None) -> AsyncMock:
    """Mock AsyncSession: first execute → upsert row; subsequent → group rows."""
    db = AsyncMock()
    upsert_row = MagicMock()
    upsert_row.__getitem__ = MagicMock(return_value=upsert_user_id or uuid.uuid4())
    upsert_result = MagicMock()
    upsert_result.fetchone.return_value = upsert_row

    group_result = MagicMock()
    group_result.fetchall.return_value = [(gid,) for gid in (group_ids or [])]

    db.execute.side_effect = [upsert_result, group_result]
    return db


def _get_oidc_module(monkeypatch):
    """Return freshly reloaded oidc module with OIDC env vars set."""
    for k, v in _OIDC_ENV.items():
        monkeypatch.setenv(k, v)
    if "backend.auth.oidc" in sys.modules:
        del sys.modules["backend.auth.oidc"]
    import backend.auth.oidc as oidc_mod  # noqa: PLC0415
    return oidc_mod


# ---------------------------------------------------------------------------
# T002 criterion: test_missing_env_var_raises_runtime_error
# ---------------------------------------------------------------------------

def test_missing_env_var_raises_runtime_error(monkeypatch):
    """Module import raises RuntimeError when OIDC_ISSUER is absent."""
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("OIDC_JWKS_URI", raising=False)
    if "backend.auth.oidc" in sys.modules:
        del sys.modules["backend.auth.oidc"]
    with pytest.raises(RuntimeError, match="Missing required env var"):
        import backend.auth.oidc  # noqa: F401, PLC0415


# ---------------------------------------------------------------------------
# T003 criteria: verify_oidc_token tests
# ---------------------------------------------------------------------------

async def test_valid_bearer_returns_authenticated_user(monkeypatch):
    """Happy path: valid RS256 JWT → AuthenticatedUser with auth_type='oidc'."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(groups=["engineers"])
    user_id = uuid.uuid4()
    db = _make_db(upsert_user_id=user_id, group_ids=[42])

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        result = await oidc_mod.verify_oidc_token(_make_request(), token, db)

    assert result.auth_type == "oidc"
    assert result.user_id == user_id
    assert result.user_group_ids == [42]


async def test_expired_token_returns_401(monkeypatch):
    """Expired JWT → 401 AUTH_TOKEN_INVALID."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(exp_offset=-60)  # already expired

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oidc_mod.verify_oidc_token(_make_request(), token, AsyncMock())
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_TOKEN_INVALID"


async def test_wrong_issuer_returns_401(monkeypatch):
    """JWT with wrong iss → 401 AUTH_TOKEN_INVALID."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(iss="https://evil.example.com")

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oidc_mod.verify_oidc_token(_make_request(), token, AsyncMock())
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_TOKEN_INVALID"


async def test_wrong_audience_returns_401(monkeypatch):
    """JWT with wrong aud → 401 AUTH_TOKEN_INVALID."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(aud="wrong-audience")

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oidc_mod.verify_oidc_token(_make_request(), token, AsyncMock())
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_TOKEN_INVALID"


async def test_bad_signature_returns_401(monkeypatch):
    """JWT signed with different key → 401 AUTH_TOKEN_INVALID."""
    oidc_mod = _get_oidc_module(monkeypatch)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _make_token(private_key=other_key)

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oidc_mod.verify_oidc_token(_make_request(), token, AsyncMock())
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_TOKEN_INVALID"


async def test_unknown_kid_refreshes_cache_then_fails(monkeypatch):
    """Unknown kid triggers cache refresh; if still not found → 401."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(kid="unknown-kid-xyz")

    async def mock_refresh():
        pass  # refresh does NOT add the key

    with patch.object(oidc_mod, "_refresh_jwks_cache", side_effect=mock_refresh):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oidc_mod.verify_oidc_token(_make_request(), token, AsyncMock())
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"]["code"] == "AUTH_TOKEN_INVALID"


async def test_empty_groups_returns_empty_user_group_ids(monkeypatch):
    """groups=[] in JWT → user_group_ids=[] without error (D06 permissive)."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(groups=[])
    db = _make_db(group_ids=[])

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        result = await oidc_mod.verify_oidc_token(_make_request(), token, db)

    assert result.user_group_ids == []
    assert result.auth_type == "oidc"


async def test_absent_groups_returns_empty_user_group_ids(monkeypatch):
    """No 'groups' claim in JWT → user_group_ids=[] without error (D06 permissive)."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(groups=None)  # groups key absent from payload
    db = _make_db(group_ids=[])

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        result = await oidc_mod.verify_oidc_token(_make_request(), token, db)

    assert result.user_group_ids == []


async def test_jit_upsert_called_on_new_user(monkeypatch):
    """First login: db.execute called for INSERT (upsert) + SELECT (groups)."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(groups=["engineers"])  # non-empty so group SELECT fires
    db = _make_db(group_ids=[1])

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        await oidc_mod.verify_oidc_token(_make_request(), token, db)

    # execute called twice: upsert + group resolution
    assert db.execute.call_count == 2
    upsert_call_sql = str(db.execute.call_args_list[0][0][0])
    assert "INSERT INTO users" in upsert_call_sql
    assert "ON CONFLICT" in upsert_call_sql


async def test_jit_upsert_updates_email_on_existing_user(monkeypatch):
    """ON CONFLICT path: UPDATE email and display_name present in SQL."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(groups=[])
    db = _make_db()

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        await oidc_mod.verify_oidc_token(_make_request(), token, db)

    upsert_call_sql = str(db.execute.call_args_list[0][0][0])
    assert "DO UPDATE" in upsert_call_sql
    assert "email" in upsert_call_sql
    assert "display_name" in upsert_call_sql


async def test_error_does_not_expose_token_content(monkeypatch):
    """401 error detail must not contain any JWT payload fields (AC4)."""
    oidc_mod = _get_oidc_module(monkeypatch)
    token = _make_token(exp_offset=-60)

    with patch.object(oidc_mod, "_get_jwks_key", return_value=_PUBLIC_KEY):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await oidc_mod.verify_oidc_token(_make_request(), token, AsyncMock())

    detail_str = str(exc_info.value.detail)
    # Must not contain any identifiable token content
    assert "user-sub-001" not in detail_str
    assert "user@brysen.test" not in detail_str
    assert "brysen" not in detail_str or "AUTH_TOKEN_INVALID" in detail_str


async def test_jwks_cache_ttl_respected(monkeypatch):
    """Simulating TTL expiry causes _refresh_jwks_cache to be called again."""
    oidc_mod = _get_oidc_module(monkeypatch)
    # Pre-populate cache with the test key
    oidc_mod._jwks_cache = {_KID: _PUBLIC_KEY}
    # Set fetched_at to far in the past (simulate TTL expired)
    oidc_mod._jwks_fetched_at = 0.0

    refresh_called = []

    async def mock_refresh():
        refresh_called.append(True)
        oidc_mod._jwks_cache = {_KID: _PUBLIC_KEY}
        oidc_mod._jwks_fetched_at = time.monotonic()

    token = _make_token(groups=[])
    db = _make_db()

    with patch.object(oidc_mod, "_refresh_jwks_cache", side_effect=mock_refresh):
        with patch.object(oidc_mod, "_get_jwks_key", wraps=oidc_mod._get_jwks_key):
            await oidc_mod.verify_oidc_token(_make_request(), token, db)

    assert len(refresh_called) >= 1, "Cache refresh should be triggered on TTL expiry"


def test_no_rag_api_import():
    """A001: backend.auth.oidc must not import backend.rag or backend.api (static check)."""
    import ast, pathlib
    src = pathlib.Path("backend/auth/oidc.py").read_text()
    tree = ast.parse(src)
    banned = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("backend.rag") or node.module.startswith("backend.api"):
                banned.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("backend.rag") or alias.name.startswith("backend.api"):
                    banned.append(alias.name)
    assert not banned, f"A001 cross-boundary imports found: {banned}"
