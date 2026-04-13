# Spec: docs/llm-provider/spec/llm-provider.spec.md#S005
# Task: T014 — LLM-path tests for new QueryResponse shape (D09, D10)
# Decision: D09 — NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}
# Decision: D10 — QueryResponse: answer + sources + low_confidence (no results[])
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.query import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.rag.llm import LLMResponse, NoRelevantChunksError
from backend.rag.retriever import RetrievedDocument


# ---------------------------------------------------------------------------
# Helpers (mirrors test_query_rbac.py pattern)
# ---------------------------------------------------------------------------

def _make_user(group_ids: list[int]) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=group_ids,
        auth_type="api_key",  # type: ignore[arg-type]
    )


def _make_doc(content: str = "chunk text") -> RetrievedDocument:
    return RetrievedDocument(
        doc_id=uuid.uuid4(),
        chunk_index=0,
        score=0.9,
        user_group_id=1,
        content=content,
    )


async def _noop_db():
    yield None


def _make_app(user: AuthenticatedUser) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = _noop_db
    return app


# ---------------------------------------------------------------------------
# Tests — LLM response shape (D10)
# ---------------------------------------------------------------------------

def test_query_returns_answer_and_sources():
    """D10: response shape is {answer, sources, low_confidence} not results[]."""
    user = _make_user([1])
    app = _make_app(user)
    docs = [_make_doc("context about 42")]
    llm_resp = LLMResponse(
        answer="42", sources=["doc-1"], confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False
    )

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "What is 42?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "42"
    assert body["sources"] == [str(docs[0].doc_id)]  # R002: doc_id strings, not LLM source labels
    assert body["low_confidence"] is False
    assert "results" not in body  # D10: old field removed
    assert "request_id" in body   # D12: retained for traceability


def test_query_no_chunks_returns_200_with_null_answer():
    """D09: NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}."""
    user = _make_user([1])
    app = _make_app(user)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query.generate_answer",
               new=AsyncMock(side_effect=NoRelevantChunksError("no chunks"))), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "unknown"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["reason"] == "no_relevant_chunks"
    assert body["low_confidence"] is False
    assert body["sources"] == []


def test_query_low_confidence_flagged_in_response():
    """D10: low_confidence flag surfaced in response."""
    user = _make_user([1])
    app = _make_app(user)
    docs = [_make_doc("uncertain context")]
    llm_resp = LLMResponse(
        answer="maybe", sources=["doc-1"], confidence=0.3,
        provider="ollama", model="llama3", low_confidence=True
    )

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "Q?"})

    assert resp.json()["low_confidence"] is True
