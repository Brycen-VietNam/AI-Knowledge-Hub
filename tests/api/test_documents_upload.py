# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S001
# Task: S001-T001 — import smoke test
# Task: S001-T002 — auth_type write gate (D09)
# Task: S001-T003 — input validation (lang, content size)
# Task: S001-T004 — RBAC group membership check
# Task: S001-T005 — Document INSERT + BackgroundTasks + 202
# Decision: D09 — api_key=write, OIDC=read-only
# Decision: D11 — content NOT stored in documents; passed to ingest_pipeline
# Rule: R003, R004
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.documents import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(auth_type: str = "api_key", group_ids: list[int] | None = None) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=group_ids if group_ids is not None else [1, 2],
        auth_type=auth_type,  # type: ignore[arg-type]
    )


def _make_app(user: AuthenticatedUser, db=None) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)
    return app


VALID_BODY = {
    "title": "Test Document",
    "content": "This is a valid document content.",
    "lang": "en",
    "user_group_id": 1,
}


# ---------------------------------------------------------------------------
# T001: import smoke test
# ---------------------------------------------------------------------------

def test_import_documents_router():
    from backend.api.routes.documents import router as r
    assert r is not None


# ---------------------------------------------------------------------------
# T002: auth_type write gate
# ---------------------------------------------------------------------------

def test_oidc_caller_returns_403():
    """D09: OIDC user must get 403 on POST /v1/documents."""
    user = _make_user(auth_type="oidc")
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/v1/documents", json=VALID_BODY)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_apikey_caller_passes_gate():
    """D09: API-key user must not get 403 from write gate."""
    user = _make_user(auth_type="api_key")
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    mock_doc = MagicMock()
    mock_doc.id = doc_id
    mock_doc.status = "processing"
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock):
        resp = client.post("/v1/documents", json=VALID_BODY)
    assert resp.status_code != 403


# ---------------------------------------------------------------------------
# T003: input validation
# ---------------------------------------------------------------------------

def test_empty_content_returns_422():
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    body = {**VALID_BODY, "content": ""}
    resp = client.post("/v1/documents", json=body)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_INPUT"


def test_whitespace_only_content_returns_422():
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    body = {**VALID_BODY, "content": "   \n\t  "}
    resp = client.post("/v1/documents", json=body)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_INPUT"


def test_oversized_content_returns_413():
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    body = {**VALID_BODY, "content": "x" * 100001}
    resp = client.post("/v1/documents", json=body)
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "DOC_TOO_LARGE"


def test_invalid_lang_returns_422():
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    body = {**VALID_BODY, "lang": "xx-invalid"}
    resp = client.post("/v1/documents", json=body)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_INPUT"


def test_valid_lang_passes():
    user = _make_user()
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock):
        resp = client.post("/v1/documents", json={**VALID_BODY, "lang": "ja"})
    assert resp.status_code == 202


# ---------------------------------------------------------------------------
# T004: RBAC group membership check
# ---------------------------------------------------------------------------

def test_rbac_caller_in_group_passes():
    user = _make_user(group_ids=[1, 2])
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock):
        resp = client.post("/v1/documents", json={**VALID_BODY, "user_group_id": 1})
    assert resp.status_code == 202


def test_rbac_caller_not_in_group_returns_403():
    user = _make_user(group_ids=[1, 2])
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/v1/documents", json={**VALID_BODY, "user_group_id": 99})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_rbac_public_document_passes():
    """user_group_id=None (public) allowed for any API-key caller."""
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock):
        resp = client.post("/v1/documents", json={**VALID_BODY, "user_group_id": None})
    assert resp.status_code == 202


# ---------------------------------------------------------------------------
# T005: successful upload returns 202
# ---------------------------------------------------------------------------

def test_successful_upload_returns_202():
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock) as mock_pipeline:
        resp = client.post("/v1/documents", json=VALID_BODY)
    assert resp.status_code == 202
    data = resp.json()
    assert "doc_id" in data
    assert data["status"] == "processing"


def test_successful_upload_doc_id_is_valid_uuid():
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock):
        resp = client.post("/v1/documents", json=VALID_BODY)
    assert resp.status_code == 202
    doc_id_str = resp.json()["doc_id"]
    # Must parse as valid UUID
    uuid.UUID(doc_id_str)


def test_ingest_pipeline_called_once():
    """BackgroundTasks must dispatch ingest_pipeline exactly once with (doc_id, content)."""
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    db.add = MagicMock()
    doc_id = uuid.uuid4()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing"))
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.routes.documents.ingest_pipeline", new_callable=AsyncMock) as mock_pipeline:
        resp = client.post("/v1/documents", json=VALID_BODY)
    assert resp.status_code == 202
    mock_pipeline.assert_called_once()
    call_args = mock_pipeline.call_args
    # Second arg must be the content string (D11)
    assert call_args.args[1] == VALID_BODY["content"]
