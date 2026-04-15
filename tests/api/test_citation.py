# Spec: docs/answer-citation/spec/answer-citation.spec.md#S002
# Spec: docs/citation-quality/spec/citation-quality.spec.md#S003
# Task: S002-T001 — CitationObject construction (AC1, AC2)
# Task: S002-T002 — QueryResponse citations field (AC3, AC4, AC10)
# Task: S002-T003 — Full AC coverage
# Task: citation-quality/S003-T002 — cited field integration tests
# Decision: D-CIT-01 (additive — sources unchanged), D-CIT-03 (no score filter),
#           D-CIT-05 (API layer builds CitationObject from RetrievedDocument)
# Decision: D-CQ-01 (cited default False), D-CQ-02 (fast path), D-CQ-03 (OOB ignored)
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.models.citation import CitationObject
from backend.api.routes.query import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.rag.llm import LLMResponse, NoRelevantChunksError
from backend.rag.retriever import RetrievedDocument


# ---------------------------------------------------------------------------
# Helpers (reuse pattern from test_query.py — no duplication of auth fixtures)
# ---------------------------------------------------------------------------

def _make_user(group_ids: list[int] | None = None) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=group_ids or [1],
        auth_type="api_key",  # type: ignore[arg-type]
    )


def _make_doc(
    doc_id: uuid.UUID | None = None,
    title: str = "Test Doc",
    lang: str = "en",
    source_url: str | None = None,
    chunk_index: int = 0,
    score: float = 0.85,
) -> RetrievedDocument:
    return RetrievedDocument(
        doc_id=doc_id or uuid.uuid4(),
        chunk_index=chunk_index,
        score=score,
        user_group_id=1,
        content="chunk text",
        title=title,
        lang=lang,
        source_url=source_url,
    )


async def _noop_db():
    yield None


def _make_app(user: AuthenticatedUser) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = _noop_db
    return app


def _default_llm() -> LLMResponse:
    return LLMResponse(
        answer="test answer",
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
    )


# ---------------------------------------------------------------------------
# T001 — AC1: CitationObject construction
# ---------------------------------------------------------------------------

def test_citation_object_construction():
    """AC1: CitationObject instantiates with all 6 fields; serializes correctly."""
    doc_id = str(uuid.uuid4())
    citation = CitationObject(
        doc_id=doc_id,
        title="Policy Manual",
        source_url="https://example.com/policy.pdf",
        chunk_index=2,
        score=0.9123,
        lang="en",
    )
    data = citation.model_dump()
    assert data["doc_id"] == doc_id
    assert data["title"] == "Policy Manual"
    assert data["source_url"] == "https://example.com/policy.pdf"
    assert data["chunk_index"] == 2
    assert data["score"] == 0.9123
    assert data["lang"] == "en"


# ---------------------------------------------------------------------------
# T003 — AC2: source_url nullable
# ---------------------------------------------------------------------------

def test_citation_object_no_source_url():
    """AC2: source_url=None serializes as null in JSON output."""
    citation = CitationObject(
        doc_id=str(uuid.uuid4()),
        title="Doc Without URL",
        source_url=None,
        chunk_index=0,
        score=0.75,
        lang="ja",
    )
    data = citation.model_dump()
    assert data["source_url"] is None
    # Confirm JSON serialization uses null (not missing key)
    import json
    json_str = citation.model_dump_json()
    parsed = json.loads(json_str)
    assert "source_url" in parsed
    assert parsed["source_url"] is None


# ---------------------------------------------------------------------------
# T003 — AC3: citations order matches sources order
# ---------------------------------------------------------------------------

def test_citation_order_matches_sources():
    """AC3: citations list order matches sources list — both derived from same docs list."""
    user = _make_user()
    app = _make_app(user)

    doc1_id = uuid.uuid4()
    doc2_id = uuid.uuid4()
    docs = [
        _make_doc(doc_id=doc1_id, title="Doc One", score=0.9, chunk_index=0),
        _make_doc(doc_id=doc2_id, title="Doc Two", score=0.7, chunk_index=1),
    ]

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=_default_llm())), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "ordering test"})

    assert resp.status_code == 200
    body = resp.json()
    sources = body["sources"]
    citations = body["citations"]

    # sources and citations must have same length
    assert len(citations) == len(sources)
    # position alignment: citations[i].doc_id == sources[i]
    for i, (cit, src) in enumerate(zip(citations, sources)):
        assert cit["doc_id"] == src, f"Position {i}: citation doc_id {cit['doc_id']} != source {src}"


# ---------------------------------------------------------------------------
# T003 — AC4: empty citations when no docs returned
# ---------------------------------------------------------------------------

def test_empty_citations_on_no_chunks():
    """AC4: citations=[] when search returns no documents."""
    user = _make_user()
    app = _make_app(user)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "nothing here"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["citations"] == []
    assert body["answer"] is None


# ---------------------------------------------------------------------------
# T003 — AC10: citations field is never null in response JSON
# ---------------------------------------------------------------------------

def test_citations_not_null_in_response():
    """AC10: response JSON always has 'citations' as a list — never null, never missing."""
    user = _make_user()
    app = _make_app(user)

    # Test both success path and empty-docs path
    for search_result in [[], [_make_doc()]]:
        with patch("backend.api.routes.query.search", new=AsyncMock(return_value=search_result)), \
             patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=_default_llm())), \
             patch("backend.api.routes.query._write_audit", new=AsyncMock()):
            with TestClient(app) as client:
                resp = client.post("/v1/query", json={"query": "null check"})

        assert resp.status_code == 200
        body = resp.json()
        assert "citations" in body, "citations key must always be present"
        assert body["citations"] is not None, "citations must never be null"
        assert isinstance(body["citations"], list), "citations must be a list"


# ---------------------------------------------------------------------------
# T001 — AC9: sources field still present alongside citations
# ---------------------------------------------------------------------------

def test_citations_backward_compat_sources_present():
    """AC9: response has both 'sources' (list[str]) and 'citations' (list[CitationObject])."""
    user = _make_user()
    app = _make_app(user)
    doc = _make_doc(title="Compat Doc", source_url="https://example.com/doc.pdf")

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=_default_llm())), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "compat check"})

    assert resp.status_code == 200
    body = resp.json()
    # AC9: both fields present
    assert "sources" in body, "sources field must remain (D-CIT-01 additive)"
    assert "citations" in body, "citations field must be present"
    # sources is list[str] (doc_ids)
    assert isinstance(body["sources"], list)
    assert all(isinstance(s, str) for s in body["sources"])
    # citations is list[dict] (CitationObject)
    assert isinstance(body["citations"], list)
    assert len(body["citations"]) == len(body["sources"])


# ---------------------------------------------------------------------------
# T001 — AC11: score rounded to 4 decimal places
# ---------------------------------------------------------------------------

def test_citation_score_rounded_to_4dp():
    """AC11: CitationObject.score is rounded to 4 decimal places."""
    # score with many decimals — Pydantic float passes through; verify 4dp rounding in response
    user = _make_user()
    app = _make_app(user)
    doc = _make_doc(score=0.123456789)  # raw score from retriever

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=_default_llm())), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "score precision"})

    assert resp.status_code == 200
    citation = resp.json()["citations"][0]
    score = citation["score"]
    # Must be rounded to at most 4 decimal places
    assert score == round(score, 4), f"score {score} exceeds 4dp precision"


# ---------------------------------------------------------------------------
# citation-quality/S003-T002 — cited field integration tests
# ---------------------------------------------------------------------------

def test_cited_true_when_marker_present():
    """D-CQ-01: cited=True when LLM emitted [1] marker matching this doc's position."""
    user = _make_user()
    app = _make_app(user)
    doc = _make_doc()  # content="chunk text" → goes into content_docs at index 0

    llm = LLMResponse(
        answer="See [1] for the answer.",
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
        inline_markers_present=True,
    )
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "cited doc"})

    assert resp.status_code == 200
    citation = resp.json()["citations"][0]
    assert citation["cited"] is True


def test_cited_false_when_no_markers():
    """D-CQ-02: cited=False for all docs when inline_markers_present=False (fast path)."""
    user = _make_user()
    app = _make_app(user)
    docs = [_make_doc(), _make_doc()]

    llm = LLMResponse(
        answer="General answer with no markers.",
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
        inline_markers_present=False,  # fast path — no regex
    )
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "no markers"})

    assert resp.status_code == 200
    for citation in resp.json()["citations"]:
        assert citation["cited"] is False


def test_cited_false_oob_marker():
    """D-CQ-03: [99] with 3 docs → all cited=False (OOB silently ignored)."""
    user = _make_user()
    app = _make_app(user)
    docs = [_make_doc(), _make_doc(), _make_doc()]

    llm = LLMResponse(
        answer="See [99] — this is out of bounds.",
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
        inline_markers_present=True,
    )
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=docs)), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm)), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "oob marker"})

    assert resp.status_code == 200
    for citation in resp.json()["citations"]:
        assert citation["cited"] is False


def test_cited_false_default_on_empty_citations():
    """AC6 regression: citations=[] when no docs — no cited field issues."""
    user = _make_user()
    app = _make_app(user)

    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query._write_audit", new=AsyncMock()):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "empty path"})

    assert resp.status_code == 200
    assert resp.json()["citations"] == []
