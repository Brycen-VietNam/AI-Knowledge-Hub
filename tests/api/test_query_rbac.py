# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S005
# Task: T002 — import smoke test
# Task: T003 — unit tests: OIDC path, API-key path, 0-group path
# Task: T004 — unit tests: 401 unauthenticated, timeout 504
# Task: T014 — updated assertions for D10 QueryResponse breaking change
# Decision: D04 — 0-group users → 200 not 403
# Decision: D10 — QueryResponse: results[] → answer + sources + low_confidence
# Rule: R003 — 401 on missing auth
# Rule: R007 — 504 on timeout
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.query import QueryResponse, router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.rag.llm import LLMResponse
from backend.rag.retriever import QueryTimeoutError, RetrievedDocument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(group_ids: list[int], auth_type: str = "api_key") -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=group_ids,
        auth_type=auth_type,  # type: ignore[arg-type]
    )


def _make_doc(gid: int | None, idx: int = 0) -> RetrievedDocument:
    return RetrievedDocument(
        doc_id=uuid.uuid4(),
        chunk_index=idx,
        score=0.9,
        user_group_id=gid,
        content="test content",
    )


async def _noop_db():
    """Stub DB session — unit tests mock retrieve() so no real session needed."""
    yield None


def _make_app(user: AuthenticatedUser) -> FastAPI:
    """Build a minimal FastAPI app with verify_token and get_db overridden."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = _noop_db
    return app


# ---------------------------------------------------------------------------
# T002 — Import smoke test
# ---------------------------------------------------------------------------

def test_imports():
    """Packages importable and router is wired."""
    from backend.api.routes.query import QueryRequest, QueryResponse, router  # noqa: F401
    assert router is not None


# ---------------------------------------------------------------------------
# T003 — Unit tests: OIDC path, API-key path, 0-group
# ---------------------------------------------------------------------------

def test_api_key_user_gets_own_group_docs():
    """API-key user with group_ids=[1] — D10: response has answer+sources, not results[]."""
    user = _make_user([1], auth_type="api_key")
    app = _make_app(user)
    docs = [_make_doc(1), _make_doc(1)]
    llm_resp = LLMResponse("answer", 0.9, "ollama", "llama3", False)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "hello"})

    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
    assert "results" not in body  # D10: old field removed
    assert "request_id" in body


def test_oidc_user_gets_own_group_docs():
    """OIDC user with group_ids=[2] — D10: response has answer+sources, not results[]."""
    user = _make_user([2], auth_type="oidc")
    app = _make_app(user)
    docs = [_make_doc(2)]
    llm_resp = LLMResponse("answer", 0.9, "ollama", "llama3", False)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "oidc test"})

    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
    assert "results" not in body  # D10


def test_zero_group_user_returns_200_not_403():
    """0-group user gets 200 with answer. Never 403 (D04)."""
    user = _make_user([])
    app = _make_app(user)
    docs = [_make_doc(None)]  # NULL group_id = public
    llm_resp = LLMResponse("public answer", 0.9, "ollama", "llama3", False)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "public query"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "public answer"
    assert "results" not in body  # D10


def test_query_result_with_no_docs_returns_null_answer():
    """retrieve() returning [] → NoRelevantChunksError → 200 {answer: null} (D09)."""
    user = _make_user([1])
    app = _make_app(user)

    from backend.rag.llm import NoRelevantChunksError
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query.generate_answer",
               new=AsyncMock(side_effect=NoRelevantChunksError("empty"))), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "no results"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["reason"] == "no_relevant_chunks"
    assert "results" not in body  # D10


# ---------------------------------------------------------------------------
# T004 — Unit tests: 401, timeout 504
# ---------------------------------------------------------------------------

def test_unauthenticated_returns_401():
    """No auth headers → 401 AUTH_MISSING (R003)."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = _noop_db  # stub DB; auth still runs real verify_token
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post("/v1/query", json={"query": "no auth"})
    assert resp.status_code == 401


def test_query_timeout_returns_504():
    """retrieve() exceeding 1.8s → 504 QUERY_TIMEOUT (R007/P001)."""
    user = _make_user([1])
    app = _make_app(user)

    async def _slow(*args, **kwargs):
        raise QueryTimeoutError("timeout")

    with patch("backend.api.routes.query.search", new=_slow), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "slow query"})

    assert resp.status_code == 504
    body = resp.json()
    assert body["error"]["code"] == "QUERY_TIMEOUT"
    assert "request_id" in body["error"]


def test_query_asyncio_timeout_returns_504():
    """asyncio.wait_for timeout exceeded → 504 QUERY_TIMEOUT (P001/R007)."""
    user = _make_user([1])
    app = _make_app(user)

    with patch("backend.api.routes.query.asyncio.wait_for",
               new=AsyncMock(side_effect=asyncio.TimeoutError())), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "hanging query"})

    assert resp.status_code == 504
    assert resp.json()["error"]["code"] == "QUERY_TIMEOUT"


def test_request_id_in_response():
    """Every response includes a non-empty request_id (A005, D12)."""
    user = _make_user([1])
    app = _make_app(user)
    llm_resp = LLMResponse("ans", 0.9, "ollama", "llama3", False)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "test"})

    assert resp.status_code == 200
    rid = resp.json().get("request_id", "")
    assert len(rid) == 36  # UUID format


def test_query_too_long_returns_422():
    """query > 512 chars → 422 validation error (S003 input sanitization)."""
    user = _make_user([1])
    app = _make_app(user)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "x" * 513})

    assert resp.status_code == 422
