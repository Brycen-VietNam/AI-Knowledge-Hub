# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S001
# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S002
# Task: S001-T003 — Scaffold fixtures; S001-T004 — search() wire; S001-T005 — AC tests
# Task: S002-T001 — mock_generate fixture; S002-T002 — LLM wire; S002-T003/T004 — error+confidence
# Decision: D04 — 0-group users get public results (not 403)
# Decision: D09 — NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}
# Rule: R002 — sources must be doc_ids (not content)
# Rule: R006 — audit log called as BackgroundTask
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.query import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.rag.llm import LLMResponse, NoRelevantChunksError
from backend.rag.retriever import QueryTimeoutError, RetrievedDocument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(group_ids: list[int]) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=group_ids,
        auth_type="api_key",  # type: ignore[arg-type]
    )


def _make_doc(doc_id: uuid.UUID | None = None) -> RetrievedDocument:
    return RetrievedDocument(
        doc_id=doc_id or uuid.uuid4(),
        chunk_index=0,
        score=0.85,
        user_group_id=1,
        content="chunk text",
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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_with_groups():
    return _make_user([1, 2])


@pytest.fixture
def user_no_groups():
    return _make_user([])


@pytest.fixture
def sample_docs():
    return [_make_doc(), _make_doc()]


@pytest.fixture
def mock_search(sample_docs):
    """Patch search() to return 2 fake RetrievedDocument objects."""
    with patch(
        "backend.api.routes.query.search",
        new=AsyncMock(return_value=sample_docs),
    ) as m:
        yield m


@pytest.fixture
def mock_audit():
    """Patch _write_audit to avoid real DB in background tasks."""
    with patch(
        "backend.api.routes.query._write_audit",
        new=AsyncMock(),
    ) as m:
        yield m


@pytest.fixture
def default_llm_response():
    return LLMResponse(
        answer="test answer",
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
    )


@pytest.fixture
def mock_generate(default_llm_response):
    """Patch generate_answer() to return a canned LLMResponse."""
    with patch(
        "backend.api.routes.query.generate_answer",
        new=AsyncMock(return_value=default_llm_response),
    ) as m:
        yield m


# ---------------------------------------------------------------------------
# T003 stub tests (filled in T005)
# ---------------------------------------------------------------------------

def test_sources_are_doc_ids(mock_search, mock_audit, mock_generate, user_with_groups, sample_docs):
    """AC: sources must be doc_id strings — never content (R002)."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json={"query": "test query"})
    assert resp.status_code == 200
    body = resp.json()
    expected_ids = {str(d.doc_id) for d in sample_docs}
    assert set(body["sources"]) == expected_ids


def test_query_request_lang_optional(user_with_groups, mock_audit):
    """AC: lang field is optional — absent defaults to None (auto-detect)."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])):
        with TestClient(app) as client:
            resp_no_lang = client.post("/v1/query", json={"query": "hello"})
            resp_with_lang = client.post("/v1/query", json={"query": "hello", "lang": "ja"})
    assert resp_no_lang.status_code == 200
    assert resp_with_lang.status_code == 200


# ---------------------------------------------------------------------------
# T005 AC tests (AC1, AC6, AC7, AC8)
# ---------------------------------------------------------------------------

def test_ac1_happy_path_returns_200(mock_search, mock_audit, mock_generate, user_with_groups, sample_docs):
    """AC1: POST /v1/query returns 200; sources are doc_id strings; answer populated."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json={"query": "What is the policy?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "test answer"
    assert set(body["sources"]) == {str(d.doc_id) for d in sample_docs}
    assert "request_id" in body
    assert isinstance(body["low_confidence"], bool)


def test_ac6_timeout_raises_query_timeout_error(mock_audit, user_with_groups):
    """AC6: asyncio.TimeoutError from search() propagates as QueryTimeoutError → 504."""
    app = _make_app(user_with_groups)
    timeout_mock = AsyncMock(side_effect=asyncio.TimeoutError())
    with patch("backend.api.routes.query.search", new=timeout_mock):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "slow query"})
    assert resp.status_code == 504
    body = resp.json()
    assert body["error"]["code"] == "QUERY_TIMEOUT"


def test_ac7_zero_group_user_gets_results(mock_audit, user_no_groups):
    """AC7: 0-group user receives public results (not 403) — D04."""
    doc = _make_doc()
    app = _make_app(user_no_groups)
    llm_resp = LLMResponse(
        answer="public answer", confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False,
    )
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "public content"})
    assert resp.status_code == 200
    assert str(doc.doc_id) in resp.json()["sources"]


def test_ac8_audit_log_called_as_background_task(mock_search, user_with_groups):
    """AC8: _write_audit is called once per request (as BackgroundTask — R006)."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query._write_audit", new=AsyncMock()) as audit_mock:
        with TestClient(app) as client:
            client.post("/v1/query", json={"query": "audit test"})
    audit_mock.assert_called_once()


# ---------------------------------------------------------------------------
# S002 tests — generate_answer() wiring (T002–T004)
# ---------------------------------------------------------------------------

def test_answer_returned_on_success(mock_search, mock_audit, mock_generate, user_with_groups):
    """S002: successful LLM call → answer populated in response."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json={"query": "What is the policy?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "test answer"


def test_no_answer_on_empty_docs(mock_audit, user_with_groups):
    """S002: empty search results → answer=null, reason=no_relevant_chunks, LLM not called (D09)."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock()) as gen_mock:
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "nothing here"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["reason"] == "no_relevant_chunks"
    gen_mock.assert_not_called()


def test_llm_timeout_returns_503(mock_search, mock_audit, user_with_groups):
    """S002: asyncio.TimeoutError from generate_answer() → 503 LLM_UNAVAILABLE."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.generate_answer",
               new=AsyncMock(side_effect=asyncio.TimeoutError())):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "slow llm"})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "LLM_UNAVAILABLE"


def test_llm_error_returns_503(mock_search, mock_audit, user_with_groups):
    """S002: LLMError from generate_answer() → 503 LLM_UNAVAILABLE."""
    from backend.rag.llm import LLMError
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.generate_answer",
               new=AsyncMock(side_effect=LLMError("provider down"))):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "broken llm"})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "LLM_UNAVAILABLE"


def test_no_relevant_chunks_200(mock_search, mock_audit, user_with_groups):
    """S002/D09: NoRelevantChunksError → 200 with answer=null, reason=no_relevant_chunks."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.generate_answer",
               new=AsyncMock(side_effect=NoRelevantChunksError("empty"))):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "no context"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["reason"] == "no_relevant_chunks"
    assert body["sources"] == []


def test_low_confidence_flag(mock_search, mock_audit, user_with_groups):
    """S002/C014: confidence < 0.4 → low_confidence=True."""
    app = _make_app(user_with_groups)
    low_conf = LLMResponse(
        answer="uncertain", confidence=0.3,
        provider="ollama", model="llama3", low_confidence=True,
    )
    with patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=low_conf)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "unsure?"})
    assert resp.json()["low_confidence"] is True


def test_high_confidence_not_flagged(mock_search, mock_audit, user_with_groups):
    """S002/C014: confidence >= 0.4 → low_confidence=False."""
    app = _make_app(user_with_groups)
    high_conf = LLMResponse(
        answer="confident", confidence=0.8,
        provider="ollama", model="llama3", low_confidence=False,
    )
    with patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=high_conf)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "sure thing"})
    assert resp.json()["low_confidence"] is False


def test_reason_field_none_on_success(mock_search, mock_audit, mock_generate, user_with_groups):
    """S002: reason field is null/absent on successful answer responses."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json={"query": "explain this"})
    body = resp.json()
    assert body["answer"] is not None
    assert body.get("reason") is None


# ---------------------------------------------------------------------------
# S004 tests — T001 validators, T003 request_id threading
# ---------------------------------------------------------------------------

def test_query_too_long_returns_422(user_with_groups):
    """AC3/S004-T001: query > 512 chars → 422 (Pydantic max_length)."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json={"query": "x" * 513})
    assert resp.status_code == 422


def test_top_k_out_of_range_returns_422(user_with_groups):
    """AC3/S004-T001: top_k=0 and top_k=101 are out of range → 422."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        assert client.post("/v1/query", json={"query": "q", "top_k": 0}).status_code == 422
        assert client.post("/v1/query", json={"query": "q", "top_k": 101}).status_code == 422


def test_control_chars_stripped_from_query(user_with_groups, mock_audit):
    """S004-T001/SECURITY S003: control chars stripped; request succeeds with clean query."""
    app = _make_app(user_with_groups)
    captured = {}

    def _side_effect(**kwargs):
        captured["query"] = kwargs.get("query", "")
        return []

    mock = AsyncMock(side_effect=_side_effect)
    with patch("backend.api.routes.query.search", new=mock):
        with TestClient(app) as client:
            client.post("/v1/query", json={"query": "hello\x00world\x1f"})

    assert "\x00" not in captured.get("query", "")
    assert "\x1f" not in captured.get("query", "")
    assert "helloworld" in captured.get("query", "")


def test_request_id_in_success_response(mock_search, mock_audit, mock_generate, user_with_groups):
    """AC6/S004-T003: request_id present and is a valid UUID in success response."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json={"query": "request id test"})
    assert resp.status_code == 200
    request_id = resp.json().get("request_id")
    assert request_id is not None
    uuid.UUID(request_id)  # raises if not a valid UUID


def test_no_stack_trace_in_error_response(user_with_groups):
    """AC2/S004-T003: error responses must not contain 'Traceback' (no stack leak)."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.search",
               new=AsyncMock(side_effect=asyncio.TimeoutError())):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "timeout query"})
    assert resp.status_code == 504
    assert "Traceback" not in resp.text
    assert "traceback" not in resp.text.lower()


# ---------------------------------------------------------------------------
# S005 tests — AC1–AC6, AC9, AC11 integration coverage
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang", ["ja", "en", "vi", "ko"])
def test_ac1_happy_path_multilang(lang, mock_audit, user_with_groups):
    """AC1 (S005-T001): Happy path returns 200 + answer for each supported language."""
    app = _make_app(user_with_groups)
    doc = _make_doc()
    llm_resp = LLMResponse(
        answer=f"answer in {lang}", confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False,
    )
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "policy question", "lang": lang})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == f"answer in {lang}"
    assert "request_id" in body


def test_ac2_rbac_group_ids_passed_to_search(mock_audit, mock_generate):
    """AC2 (S005-T001): search() is called with the user's group_ids — RBAC isolation."""
    user = _make_user([7, 8, 9])
    app = _make_app(user)
    doc = _make_doc()
    search_mock = AsyncMock(return_value=[doc])
    with patch("backend.api.routes.query.search", new=search_mock):
        with TestClient(app) as client:
            client.post("/v1/query", json={"query": "rbac check"})
    call_kwargs = search_mock.call_args.kwargs
    assert call_kwargs["user_group_ids"] == [7, 8, 9]


@pytest.mark.parametrize("payload,expected_status", [
    ({"query": "x" * 513}, 422),           # AC3a: query > 512 chars
    ({"query": "q", "top_k": 0}, 422),     # AC3b: top_k below minimum
    ({"query": "q", "top_k": 101}, 422),   # AC3c: top_k above maximum
])
def test_ac3_input_validation(payload, expected_status, user_with_groups):
    """AC3 (S005-T001): Invalid inputs return 422 — boundary enforcement."""
    app = _make_app(user_with_groups)
    with TestClient(app) as client:
        resp = client.post("/v1/query", json=payload)
    assert resp.status_code == expected_status


def test_ac4_no_auth_returns_401():
    """AC4 (S005-T001): Missing auth header → 401 (verify_token real; get_db stubbed)."""
    app = FastAPI()
    app.include_router(router)
    # Override get_db only — verify_token is real and raises 401 before any DB access
    app.dependency_overrides[get_db] = _noop_db
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post("/v1/query", json={"query": "unauth"})
    assert resp.status_code == 401


def test_ac5_zero_group_user_gets_200_not_403(mock_audit, user_no_groups):
    """AC5 (S005-T001): 0-group user gets 200 with results — not 403 (D04 regression guard)."""
    app = _make_app(user_no_groups)
    doc = _make_doc()
    llm_resp = LLMResponse(
        answer="public result", confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False,
    )
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "public info"})
    assert resp.status_code == 200
    assert str(doc.doc_id) in resp.json()["sources"]


def test_ac6_request_id_in_error_response(mock_audit, user_with_groups):
    """AC6 (S005-T001): request_id is present in error response body (not just success)."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.search",
               new=AsyncMock(side_effect=asyncio.TimeoutError())):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "timeout for id check"})
    assert resp.status_code == 504
    body = resp.json()
    assert "request_id" in body["error"]
    uuid.UUID(body["error"]["request_id"])  # must be valid UUID


def test_ac9_low_confidence_flag_set(mock_search, mock_audit, user_with_groups):
    """AC9 (S005-T001): LLM returns confidence=0.3 → low_confidence=True in response."""
    app = _make_app(user_with_groups)
    low_conf = LLMResponse(
        answer="uncertain answer", confidence=0.3,
        provider="ollama", model="llama3", low_confidence=True,
    )
    with patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=low_conf)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "maybe?"})
    assert resp.status_code == 200
    assert resp.json()["low_confidence"] is True


def test_ac11_no_relevant_chunks_returns_200_null_answer(mock_search, mock_audit, user_with_groups):
    """AC11 (S005-T001): NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}."""
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.generate_answer",
               new=AsyncMock(side_effect=NoRelevantChunksError("nothing"))):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "obscure topic"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["reason"] == "no_relevant_chunks"


# ---------------------------------------------------------------------------
# S005 / answer-citation T002 — AC9, AC10, AC11 integration (citations field)
# ---------------------------------------------------------------------------

def _make_enriched_doc(doc_id=None):
    """RetrievedDocument with title/lang/source_url populated (answer-citation S001)."""
    return RetrievedDocument(
        doc_id=doc_id or uuid.uuid4(),
        chunk_index=0,
        score=0.85,
        user_group_id=1,
        content="chunk text",
        title="Integration Doc",
        lang="en",
        source_url="https://example.com/doc.pdf",
    )


def test_query_response_has_citations_and_sources(mock_audit, user_with_groups):
    """AC9 (T002): /v1/query response contains both 'sources' and 'citations' fields."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC9
    # Decision: D-CIT-01 — additive; sources unchanged
    app = _make_app(user_with_groups)
    doc = _make_enriched_doc()
    llm_resp = LLMResponse(answer="ok", confidence=0.9, provider="ollama", model="llama3", low_confidence=False)
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "test"})
    assert resp.status_code == 200
    body = resp.json()
    assert "sources" in body
    assert "citations" in body
    assert isinstance(body["sources"], list)
    assert isinstance(body["citations"], list)
    assert len(body["citations"]) == len(body["sources"])


def test_query_response_citations_not_null(mock_audit, user_with_groups):
    """AC10 (T002): citations is always a list — never null, even with empty results."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC10
    app = _make_app(user_with_groups)
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[])):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "nothing"})
    assert resp.status_code == 200
    body = resp.json()
    assert "citations" in body
    assert body["citations"] is not None
    assert isinstance(body["citations"], list)


def test_query_response_citation_fields_complete(mock_audit, user_with_groups):
    """AC11 (T002): each CitationObject has all 6 required fields with correct types."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC11
    # Fields: doc_id(str), title(str), source_url(str|None), chunk_index(int), score(float), lang(str)
    app = _make_app(user_with_groups)
    doc = _make_enriched_doc()
    llm_resp = LLMResponse(answer="ok", confidence=0.9, provider="ollama", model="llama3", low_confidence=False)
    with patch("backend.api.routes.query.search", new=AsyncMock(return_value=[doc])), \
         patch("backend.api.routes.query.generate_answer", new=AsyncMock(return_value=llm_resp)):
        with TestClient(app) as client:
            resp = client.post("/v1/query", json={"query": "fields check"})
    assert resp.status_code == 200
    citation = resp.json()["citations"][0]
    assert isinstance(citation["doc_id"], str)
    assert isinstance(citation["title"], str)
    assert citation["source_url"] is None or isinstance(citation["source_url"], str)
    assert isinstance(citation["chunk_index"], int)
    assert isinstance(citation["score"], float)
    assert isinstance(citation["lang"], str)
