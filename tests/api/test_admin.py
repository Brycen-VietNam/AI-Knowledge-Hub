# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T011 — tests for /v1/admin/* endpoints and /v1/metrics (AC4–AC15, D09, D10)
# Rule: R003 — every admin endpoint tested with admin auth AND non-admin (403 gate)
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.admin import router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="oidc",
        is_admin=True,
    )


def _non_admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        user_group_ids=[1],
        auth_type="oidc",
        is_admin=False,
    )


def _make_app(user: AuthenticatedUser, db) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)
    return app


def _scalar_mock(value) -> MagicMock:
    m = MagicMock()
    m.scalar.return_value = value
    return m


def _mappings_mock(rows: list[dict]) -> MagicMock:
    m = MagicMock()
    mock_rows = []
    for row in rows:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        r.get = lambda k, default=None, _row=row: _row.get(k, default)
        mock_rows.append(r)
    m.mappings.return_value.all.return_value = mock_rows
    return m


def _mappings_first_mock(row: dict | None) -> MagicMock:
    m = MagicMock()
    if row is None:
        m.mappings.return_value.first.return_value = None
    else:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        m.mappings.return_value.first.return_value = r
    return m


def _fetchone_mock(value) -> MagicMock:
    m = MagicMock()
    m.fetchone.return_value = value
    return m


# ---------------------------------------------------------------------------
# T011: Admin document endpoints (AC4, AC5, AC15)
# ---------------------------------------------------------------------------

class TestAdminDocuments:
    def test_list_all_documents_admin(self):
        """AC4: admin gets all documents without RBAC filter."""
        user = _admin_user()
        db = AsyncMock()
        doc_id = uuid.uuid4()
        row = {
            "id": doc_id, "title": "Doc A", "lang": "en",
            "user_group_id": 1, "status": "ready",
            "created_at": MagicMock(isoformat=lambda: "2026-04-17T00:00:00"),
            "chunk_count": 2,
        }
        db.execute = AsyncMock(side_effect=[_mappings_mock([row]), _scalar_mock(1)])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/documents")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(doc_id)

    def test_list_documents_non_admin_returns_403(self):
        """AC15: non-admin gets 403 on /v1/admin/documents."""
        user = _non_admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/documents")
        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"

    def test_list_documents_limit_over_100_returns_422(self):
        user = _admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/documents?limit=101")
        assert resp.status_code == 422

    def test_delete_document_admin_ok(self):
        """AC5: admin can delete any document."""
        user = _admin_user()
        db = AsyncMock()
        doc_id = uuid.uuid4()
        db.execute = AsyncMock(side_effect=[_fetchone_mock(("row",)), MagicMock()])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        with patch("backend.api.routes.admin._write_audit_log", new=AsyncMock()):
            resp = client.delete(f"/v1/admin/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == str(doc_id)

    def test_delete_document_not_found_returns_404(self):
        """AC5: 404 when document does not exist."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/documents/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_delete_document_non_admin_returns_403(self):
        """AC15: non-admin cannot delete via admin route."""
        user = _non_admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/documents/{uuid.uuid4()}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# T011: Group CRUD (AC6–AC9)
# ---------------------------------------------------------------------------

class TestAdminGroups:
    def test_list_groups_admin(self):
        """AC6: admin lists all groups with user_count."""
        user = _admin_user()
        db = AsyncMock()
        row = {
            "id": 1, "name": "admins", "is_admin": True,
            "created_at": MagicMock(isoformat=lambda: "2026-01-01T00:00:00"),
            "user_count": 2,
        }
        db.execute = AsyncMock(return_value=_mappings_mock([row]))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/groups")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "admins"
        assert data["items"][0]["user_count"] == 2

    def test_list_groups_non_admin_returns_403(self):
        """AC15: non-admin cannot list groups."""
        user = _non_admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/groups")
        assert resp.status_code == 403

    def test_create_group_returns_201(self):
        """AC7: admin creates group, gets 201 with full row."""
        user = _admin_user()
        db = AsyncMock()
        row = {
            "id": 5, "name": "editors", "is_admin": False,
            "created_at": MagicMock(isoformat=lambda: "2026-04-17T00:00:00"),
        }
        db.execute = AsyncMock(return_value=_mappings_first_mock(row))
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/groups", json={"name": "editors", "is_admin": False})
        assert resp.status_code == 201
        assert resp.json()["name"] == "editors"

    def test_update_group_name(self):
        """AC8: admin updates group name."""
        user = _admin_user()
        db = AsyncMock()
        row = {
            "id": 1, "name": "renamed", "is_admin": False,
            "created_at": MagicMock(isoformat=lambda: "2026-01-01T00:00:00"),
        }
        db.execute = AsyncMock(return_value=_mappings_first_mock(row))
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.put("/v1/admin/groups/1", json={"name": "renamed"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "renamed"

    def test_update_group_no_fields_returns_422(self):
        """AC8: empty body returns 422."""
        user = _admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.put("/v1/admin/groups/1", json={})
        assert resp.status_code == 422

    def test_delete_group_ok(self):
        """AC9: admin deletes group with no users."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),  # exists check
            _scalar_mock(0),           # member_count = 0
            MagicMock(),               # DELETE
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/v1/admin/groups/1")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 1

    def test_delete_group_has_users_returns_409(self):
        """AC9: 409 when group still has users."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),  # exists check
            _scalar_mock(3),           # member_count = 3
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/v1/admin/groups/1")
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "GROUP_HAS_USERS"

    def test_delete_group_not_found_returns_404(self):
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/v1/admin/groups/999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# T011: User endpoints (AC10–AC12, D10)
# ---------------------------------------------------------------------------

class TestAdminUsers:
    def test_list_users_admin(self):
        """AC10: admin lists all users with groups."""
        user = _admin_user()
        db = AsyncMock()
        uid = uuid.uuid4()
        row = {
            "id": uid, "sub": "user@test.com", "email": "user@test.com",
            "display_name": "Test User", "is_active": True, "groups": [],
        }
        db.execute = AsyncMock(return_value=_mappings_mock([row]))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["sub"] == "user@test.com"

    def test_list_users_non_admin_returns_403(self):
        """AC15: non-admin cannot list users."""
        user = _non_admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/users")
        assert resp.status_code == 403

    def test_update_user_active_toggle(self):
        """D10: admin toggles user is_active."""
        user = _admin_user()
        db = AsyncMock()
        uid = uuid.uuid4()
        row = {"id": uid, "sub": "user@test.com", "is_active": False}
        db.execute = AsyncMock(return_value=_mappings_first_mock(row))
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.put(f"/v1/admin/users/{uid}", json={"is_active": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_update_user_not_found_returns_404(self):
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_mappings_first_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.put(f"/v1/admin/users/{uuid.uuid4()}", json={"is_active": True})
        assert resp.status_code == 404

    def test_assign_user_groups_ok(self):
        """AC11: admin assigns user to groups."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock())
        db.commit = AsyncMock()
        uid = uuid.uuid4()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{uid}/groups", json={"group_ids": [1, 2]})
        assert resp.status_code == 200
        assert resp.json()["group_ids"] == [1, 2]

    def test_assign_user_groups_empty_returns_422(self):
        """AC11: empty group_ids returns 422."""
        user = _admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{uuid.uuid4()}/groups", json={"group_ids": []})
        assert resp.status_code == 422

    def test_remove_user_group_ok(self):
        """AC12: admin removes user from group."""
        user = _admin_user()
        db = AsyncMock()
        uid = uuid.uuid4()
        remove_result = MagicMock()
        remove_result.fetchone.return_value = ("row",)
        db.execute = AsyncMock(return_value=remove_result)
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{uid}/groups/1")
        assert resp.status_code == 200
        assert resp.json()["removed_group_id"] == 1

    def test_remove_user_group_not_found_returns_404(self):
        """AC12: 404 when membership doesn't exist."""
        user = _admin_user()
        db = AsyncMock()
        remove_result = MagicMock()
        remove_result.fetchone.return_value = None
        db.execute = AsyncMock(return_value=remove_result)

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{uuid.uuid4()}/groups/99")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# T011: GET /v1/metrics (D09)
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_get_metrics_admin(self):
        """D09: admin gets system metrics."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[
            _scalar_mock(42),   # document_count
            _scalar_mock(10),   # active_users_count
            _scalar_mock(150),  # query_count_24h
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_count"] == 42
        assert data["active_users_count"] == 10
        assert data["query_count_24h"] == 150
        assert data["health"] == "ok"

    def test_get_metrics_non_admin_returns_403(self):
        """D09/AC15: non-admin cannot access /v1/metrics."""
        user = _non_admin_user()
        db = AsyncMock()
        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/metrics")
        assert resp.status_code == 403
