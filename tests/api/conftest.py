# Stub OIDC env vars so backend.auth.oidc can be imported in unit tests
# without a real OIDC provider. Values are intentionally invalid — tests
# override verify_token via dependency injection and never call verify_oidc_token.
# AUTH_SECRET_KEY set here (before any test module import) so _LOCAL_SECRET in
# backend.auth.dependencies is populated regardless of test collection order.
import asyncio
import os

import pytest

os.environ.setdefault("OIDC_ISSUER", "https://test.example.com")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("OIDC_JWKS_URI", "https://test.example.com/.well-known/jwks.json")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key-for-unit-tests-only-32bytes!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-key-for-unit-tests-32b!")

_TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "")
_integration_available = bool(_TEST_DB_URL)

# Set DB/Redis env vars early so backend.db.session and app init pick them up correctly.
if _integration_available:
    os.environ.setdefault("DATABASE_URL", _TEST_DB_URL)
    os.environ.setdefault("REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379"))


_INTEGRATION_USER_ID = "00000000-0000-0000-0000-000000000001"


def _seed_integration_user():
    """Ensure test user exists in DB (audit_logs FK requires valid user_id)."""
    import asyncio
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    async def _run():
        engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(text("""
                INSERT INTO users (id, sub, email, display_name)
                VALUES (CAST(:id AS uuid), :sub, :email, :name)
                ON CONFLICT (id) DO NOTHING
            """).bindparams(
                id=_INTEGRATION_USER_ID,
                sub="integration-test",
                email="integration@test.local",
                name="Integration Test User",
            ))
        await engine.dispose()

    asyncio.run(_run())


@pytest.fixture
def integration_client():
    """TestClient wired to the live DB for @pytest.mark.integration tests."""
    if not _integration_available:
        pytest.skip("TEST_DATABASE_URL not set — skipping integration test")

    _seed_integration_user()

    from fastapi.testclient import TestClient
    from backend.api.app import app
    from backend.auth.types import AuthenticatedUser
    from backend.auth.dependencies import verify_token

    user = AuthenticatedUser(user_id=_INTEGRATION_USER_ID, user_group_ids=[1], auth_type="api_key")
    app.dependency_overrides[verify_token] = lambda: user

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()
