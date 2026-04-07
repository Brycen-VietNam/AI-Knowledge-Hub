# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S005-api
# Task: S005-api-T001 — GET /v1/documents (paginated, RBAC-filtered list)
# Task: S005-api-T002 — GET /v1/documents/{id} (metadata + 404)
# Task: S005-api-T003 — DELETE /v1/documents/{id} (204 + 404)
# Rule: R001 — RBAC at WHERE clause; R003 — auth required; R004 — /v1/ prefix
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.documents import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser


def _make_user(group_ids: list[int] | None = None) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=group_ids if group_ids is not None else [1],
        auth_type="api_key",  # type: ignore[arg-type]
    )


def _make_app(user: AuthenticatedUser, db) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)
    return app


# ---------------------------------------------------------------------------
# T001: GET /v1/documents — list
# ---------------------------------------------------------------------------

def test_list_documents_empty_result():
    user = _make_user()
    db = AsyncMock()

    # Mock execute for both queries (list + count)
    empty_mappings = MagicMock()
    empty_mappings.mappings.return_value.all.return_value = []
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    db.execute = AsyncMock(side_effect=[empty_mappings, count_result])

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20


def test_list_documents_limit_over_100_returns_422():
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/v1/documents?limit=101")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_INPUT"


def test_list_documents_returns_items():
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    doc_id = uuid.uuid4()

    row = MagicMock()
    row.__getitem__ = lambda self, k: {
        "id": doc_id, "title": "Doc A", "lang": "en",
        "user_group_id": 1, "status": "ready",
        "created_at": MagicMock(isoformat=lambda: "2026-04-07T00:00:00"),
        "chunk_count": 3,
    }[k]

    list_result = MagicMock()
    list_result.mappings.return_value.all.return_value = [row]
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    db.execute = AsyncMock(side_effect=[list_result, count_result])

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


# ---------------------------------------------------------------------------
# T002: GET /v1/documents/{id}
# ---------------------------------------------------------------------------

def test_get_document_not_found_returns_404():
    user = _make_user()
    db = AsyncMock()
    result = MagicMock()
    result.mappings.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=result)

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(f"/v1/documents/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_get_document_wrong_group_returns_404():
    """R001 + enumeration prevention: inaccessible doc returns 404, not 403."""
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    # RBAC WHERE filters it out → returns None
    result = MagicMock()
    result.mappings.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=result)

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(f"/v1/documents/{uuid.uuid4()}")
    assert resp.status_code == 404  # not 403


def test_get_document_success():
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    doc_id = uuid.uuid4()

    row = MagicMock()
    row.__getitem__ = lambda self, k: {
        "id": doc_id, "title": "My Doc", "lang": "ja",
        "user_group_id": 1, "status": "ready",
        "created_at": MagicMock(isoformat=lambda: "2026-04-07T00:00:00"),
        "chunk_count": 5,
    }[k]
    result = MagicMock()
    result.mappings.return_value.first.return_value = row
    db.execute = AsyncMock(return_value=result)

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(f"/v1/documents/{doc_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "My Doc"
    assert data["lang"] == "ja"
    assert data["chunk_count"] == 5


# ---------------------------------------------------------------------------
# T003: DELETE /v1/documents/{id}
# ---------------------------------------------------------------------------

def test_delete_document_not_found_returns_404():
    user = _make_user()
    db = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = None
    db.execute = AsyncMock(return_value=result)

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.delete(f"/v1/documents/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_inaccessible_doc_returns_404():
    """R001: RBAC in DELETE WHERE clause — inaccessible returns 404, not 403."""
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = None
    db.execute = AsyncMock(return_value=result)

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.delete(f"/v1/documents/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_document_success_returns_204():
    user = _make_user(group_ids=[1])
    db = AsyncMock()
    doc_id = uuid.uuid4()
    result = MagicMock()
    result.fetchone.return_value = (doc_id,)
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.delete(f"/v1/documents/{doc_id}")
    assert resp.status_code == 204
    assert resp.content == b""
