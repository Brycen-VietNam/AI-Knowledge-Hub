# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S003
# Task: S003-T001 — test scaffold; S003-T004 — AC test bodies
# Rule: S004 — 60 req/min per user_id sliding window (not fixed bucket)
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.api.middleware.rate_limiter import RateLimiter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_valkey():
    """Patches Valkey client; returns controllable mock for ZADD/ZCOUNT.

    Pipeline command methods (zadd, zremrangebyscore, zcount) are synchronous
    in a Valkey pipeline — they queue commands; only execute() is awaited.
    """
    client = MagicMock()
    pipeline = MagicMock()
    pipeline.__aenter__ = AsyncMock(return_value=pipeline)
    pipeline.__aexit__ = AsyncMock(return_value=False)
    # These are sync in pipeline context — just queue commands
    pipeline.zadd = MagicMock()
    pipeline.zremrangebyscore = MagicMock()
    pipeline.zcount = MagicMock()
    pipeline.execute = AsyncMock(return_value=[1, 0, 0])
    client.pipeline = MagicMock(return_value=pipeline)
    return client, pipeline


# ---------------------------------------------------------------------------
# AC1 — 60th request allowed, 61st returns 429
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_60th_request_allowed(mock_valkey):
    """AC1a: The 60th request within the window is allowed (count=59 before this call)."""
    client, pipeline = mock_valkey
    pipeline.execute = AsyncMock(return_value=[1, 0, 60])  # [zadd, zremrange, zcount=60]

    limiter = RateLimiter(resource="query", limit=60, window=60)
    allowed, remaining, _ = await limiter.check("user-001", client)

    assert allowed is True
    assert remaining == 0  # 60 - 60 = 0


@pytest.mark.asyncio
async def test_61st_request_denied(mock_valkey):
    """AC1b: The 61st request within the window is denied (count=60 after add)."""
    client, pipeline = mock_valkey
    pipeline.execute = AsyncMock(return_value=[1, 0, 61])  # [zadd, zremrange, zcount=61]

    limiter = RateLimiter(resource="query", limit=60, window=60)
    allowed, remaining, _ = await limiter.check("user-001", client)

    assert allowed is False
    assert remaining == 0


# ---------------------------------------------------------------------------
# AC2 — Sliding window (not fixed bucket)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sliding_window_not_fixed_bucket(mock_valkey):
    """AC2: zremrangebyscore is called to trim old entries — confirms sliding window."""
    client, pipeline = mock_valkey
    pipeline.execute = AsyncMock(return_value=[1, 3, 5])

    limiter = RateLimiter(resource="query", limit=60, window=60)
    await limiter.check("user-sliding", client)

    pipeline.zremrangebyscore.assert_called_once()
    # First arg is the key; 2nd is 0 (min); 3rd is the window start cutoff
    args = pipeline.zremrangebyscore.call_args[0]
    assert args[1] == 0  # min score always 0


# ---------------------------------------------------------------------------
# AC3 — valkey import, not redis
# ---------------------------------------------------------------------------

def test_valkey_import_not_redis():
    """AC3: rate_limiter.py must import from valkey, not redis."""
    import importlib
    import inspect
    import backend.api.middleware.rate_limiter as mod
    src = inspect.getsource(mod)
    assert "import valkey" in src or "from valkey" in src
    assert "import redis" not in src and "from redis" not in src


# ---------------------------------------------------------------------------
# AC4 — Key includes user_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_key_includes_user_id(mock_valkey):
    """AC4: Valkey key pattern is ratelimit:{resource}:{user_id}."""
    client, pipeline = mock_valkey
    pipeline.execute = AsyncMock(return_value=[1, 0, 1])

    limiter = RateLimiter(resource="query", limit=60, window=60)
    await limiter.check("user-abc123", client)

    zadd_args = pipeline.zadd.call_args[0]
    key = zadd_args[0]
    assert key == "ratelimit:query:user-abc123"


# ---------------------------------------------------------------------------
# AC5 — RateLimiter is parametric
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limiter_parametric(mock_valkey):
    """AC5: limit and window are constructor params — not hardcoded."""
    client, pipeline = mock_valkey
    pipeline.execute = AsyncMock(return_value=[1, 0, 5])

    limiter = RateLimiter(resource="docs", limit=20, window=30)
    assert limiter.limit == 20
    assert limiter.window == 30
    assert limiter.resource == "docs"

    allowed, remaining, _ = await limiter.check("user-x", client)
    assert allowed is True
    assert remaining == 15  # 20 - 5


# ---------------------------------------------------------------------------
# AC6 — Fail-open on Valkey error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fail_open_on_valkey_error():
    """AC6: Valkey error → request allowed (fail-open); warning is logged."""
    client = MagicMock()
    pipeline = MagicMock()
    pipeline.__aenter__ = AsyncMock(return_value=pipeline)
    pipeline.__aexit__ = AsyncMock(return_value=False)
    pipeline.execute = AsyncMock(side_effect=ConnectionError("valkey down"))
    client.pipeline = MagicMock(return_value=pipeline)

    limiter = RateLimiter(resource="query", limit=60, window=60)

    with patch("backend.api.middleware.rate_limiter.logger") as mock_logger:
        allowed, remaining, _ = await limiter.check("user-fail", client)

    assert allowed is True          # fail-open: request NOT rejected
    assert remaining == 60          # full limit returned on error
    mock_logger.warning.assert_called_once()


# ---------------------------------------------------------------------------
# AC7 — Rate-limit headers present on 200 response
# ---------------------------------------------------------------------------

def test_rate_limit_headers_present():
    """AC7: X-RateLimit-Remaining and X-RateLimit-Reset present on 200 /v1/query responses."""
    import uuid
    from unittest.mock import AsyncMock, patch
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.api.routes.query import router
    from backend.auth.dependencies import get_db, verify_token
    from backend.auth.types import AuthenticatedUser
    from backend.rag.llm import LLMResponse
    from backend.rag.retriever import RetrievedDocument

    user = AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="api_key",  # type: ignore[arg-type]
    )
    doc = RetrievedDocument(
        doc_id=uuid.uuid4(), chunk_index=0, score=0.9,
        user_group_id=1, content="ctx",
    )
    llm_resp = LLMResponse(
        answer="ok", confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False
    )

    mock_rl = AsyncMock(return_value=(True, 59, int(time.time()) + 60))

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield None)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=([doc], "en"))), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()), \
         patch("backend.api.routes.query._rate_limiter.check", new=mock_rl):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "test"})

    assert resp.status_code == 200
    assert "x-ratelimit-remaining" in resp.headers
    assert "x-ratelimit-reset" in resp.headers


# ---------------------------------------------------------------------------
# AC10 — Rate limit exceeded → 429 via route-level mock (S005-T002)
# ---------------------------------------------------------------------------

def test_ac10_rate_limit_exceeded_returns_429():
    """AC10 (S005-T002): patch _rate_limiter.check to (False, 0, ts) → 429 RATE_LIMIT_EXCEEDED."""
    import uuid
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.api.routes.query import router
    from backend.auth.dependencies import get_db, verify_token
    from backend.auth.types import AuthenticatedUser

    user = AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="api_key",  # type: ignore[arg-type]
    )
    reset_ts = int(time.time()) + 60
    mock_rl = AsyncMock(return_value=(False, 0, reset_ts))

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield None)

    with patch("backend.api.routes.query._rate_limiter.check", new=mock_rl):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "exceeded"})

    assert resp.status_code == 429
    body = resp.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "request_id" in body["error"]
    assert resp.headers.get("x-ratelimit-remaining") == "0"


def test_ac10_rate_limit_not_exceeded_returns_200_with_remaining():
    """AC10 complement (S005-T002): check returns (True, 59, ts) → 200 + X-RateLimit-Remaining: 59."""
    import uuid
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.api.routes.query import router
    from backend.auth.dependencies import get_db, verify_token
    from backend.auth.types import AuthenticatedUser
    from backend.rag.llm import LLMResponse
    from backend.rag.retriever import RetrievedDocument

    user = AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="api_key",  # type: ignore[arg-type]
    )
    doc = RetrievedDocument(
        doc_id=uuid.uuid4(), chunk_index=0, score=0.9,
        user_group_id=1, content="ctx",
    )
    llm_resp = LLMResponse(
        answer="ok", confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False,
    )
    reset_ts = int(time.time()) + 60
    mock_rl = AsyncMock(return_value=(True, 59, reset_ts))

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield None)

    with patch("backend.api.routes.query._rate_limiter.check", new=mock_rl), \
         patch("backend.api.routes.query.search", new=AsyncMock(return_value=([doc], "en"))), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "within limit"})

    assert resp.status_code == 200
    assert resp.headers.get("x-ratelimit-remaining") == "59"
