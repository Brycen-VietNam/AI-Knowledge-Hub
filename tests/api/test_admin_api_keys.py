# Spec: docs/user-management/spec/user-management.spec.md#S003
# Task: S003/T003 — Tests: generate_api_key happy path + error cases (AC1–AC9)
# Rule: R003 — endpoint tested with admin AND non-admin (403 gate)
# Rule: S005 — key_hash != plaintext; plaintext never in DB
# Rule: A005 — 404 body matches {"error": {"code", "message", "request_id"}}
import hashlib
import re
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.admin import ApiKeyCreate, _generate_api_key, router
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


def _fetchone_mock(value) -> MagicMock:
    m = MagicMock()
    m.fetchone.return_value = value
    return m


def _mappings_first_mock(row: dict | None) -> MagicMock:
    m = MagicMock()
    if row is None:
        m.mappings.return_value.first.return_value = None
    else:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        r.get = lambda k, default=None, _row=row: _row.get(k, default)
        m.mappings.return_value.first.return_value = r
    return m


# ---------------------------------------------------------------------------
# T001/T003: Key generation helper tests
# ---------------------------------------------------------------------------

class TestApiKeyFormat:
    def test_api_key_format(self):
        """AC: plaintext matches kh_[0-9a-f]{32}; prefix = first 8 chars."""
        plaintext, key_hash, key_prefix = _generate_api_key()
        assert re.fullmatch(r"kh_[0-9a-f]{32}", plaintext), (
            f"Plaintext key format invalid: {plaintext}"
        )
        assert key_prefix == plaintext[:8]

    def test_api_key_hash_is_sha256(self):
        """AC: key_hash is the SHA-256 hex digest of plaintext (not md5/sha1)."""
        plaintext, key_hash, key_prefix = _generate_api_key()
        expected = hashlib.sha256(plaintext.encode()).hexdigest()
        assert key_hash == expected
        assert len(key_hash) == 64  # SHA-256 hex = 64 chars

    def test_api_key_hash_differs_from_plaintext(self):
        """S005: hash must not equal plaintext."""
        plaintext, key_hash, _ = _generate_api_key()
        assert key_hash != plaintext

    def test_api_key_uniqueness(self):
        """Each call produces a different key."""
        pt1, _, _ = _generate_api_key()
        pt2, _, _ = _generate_api_key()
        assert pt1 != pt2

    def test_api_key_prefix_is_first_8_chars(self):
        """AC: prefix is exactly plaintext[:8]."""
        plaintext, _, key_prefix = _generate_api_key()
        assert key_prefix == plaintext[:8]
        assert len(key_prefix) == 8


# ---------------------------------------------------------------------------
# T002/T003: POST /v1/admin/users/{user_id}/api-keys handler tests
# ---------------------------------------------------------------------------

class TestGenerateApiKeySuccess:
    """S003/T003: AC1–AC5 — happy path."""

    def test_generate_api_key_success(self):
        """AC1: 201 with key, key_prefix, key_id, name, created_at in response."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        key_id = uuid.uuid4()

        row = {
            "id": key_id,
            "key_prefix": "kh_abcde",
            "name": "teams-bot",
            "created_at": MagicMock(isoformat=lambda: "2026-04-21T00:00:00"),
        }
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),   # user existence check
            _mappings_first_mock(row),  # INSERT RETURNING
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/v1/admin/users/{target_user_id}/api-keys",
            json={"name": "teams-bot"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert "key" in data
        assert "key_prefix" in data
        assert "key_id" in data
        assert "name" in data
        assert "created_at" in data
        assert data["key_id"] == str(key_id)
        assert data["name"] == "teams-bot"

    def test_generate_api_key_key_format_in_response(self):
        """AC: returned 'key' matches kh_[0-9a-f]{32} format."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        key_id = uuid.uuid4()

        row = {
            "id": key_id,
            "key_prefix": "kh_aaaabb",
            "name": None,
            "created_at": MagicMock(isoformat=lambda: "2026-04-21T00:00:00"),
        }
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),
            _mappings_first_mock(row),
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{target_user_id}/api-keys", json={})

        assert resp.status_code == 201
        key = resp.json()["key"]
        assert re.fullmatch(r"kh_[0-9a-f]{32}", key), f"Key format invalid: {key}"

    def test_generate_api_key_no_name(self):
        """AC5: works with no body / name=None — name is optional."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        key_id = uuid.uuid4()

        row = {
            "id": key_id,
            "key_prefix": "kh_xxxxxx",
            "name": None,
            "created_at": MagicMock(isoformat=lambda: "2026-04-21T00:00:00"),
        }
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),
            _mappings_first_mock(row),
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{target_user_id}/api-keys", json={})

        assert resp.status_code == 201
        assert resp.json()["name"] is None


class TestGenerateApiKeyHashStored:
    """S003/T003: AC6 — key_hash in DB != plaintext (S005)."""

    def test_generate_api_key_hash_stored(self):
        """key_hash stored in DB is SHA-256 of plaintext; plaintext never stored."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        key_id = uuid.uuid4()
        stored_params: dict = {}

        async def _execute_side_effect(stmt, *args, **kwargs):
            sql = str(stmt)
            # Capture INSERT bindparams from the compiled statement
            if hasattr(stmt, "_bindparams"):
                for k, v in stmt._bindparams.items():
                    stored_params[k] = v.value if hasattr(v, "value") else v
            r = MagicMock()
            r.fetchone.return_value = ("row",)
            r2 = MagicMock()
            row = {
                "id": key_id,
                "key_prefix": "kh_aabbcc",
                "name": None,
                "created_at": MagicMock(isoformat=lambda: "2026-04-21T00:00:00"),
            }
            inner = MagicMock()
            inner.__getitem__ = lambda self, k, _row=row: _row[k]
            r2.mappings.return_value.first.return_value = inner
            return r if "FROM users" in sql else r2

        db.execute = _execute_side_effect
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{target_user_id}/api-keys", json={})

        assert resp.status_code == 201
        plaintext_in_response = resp.json()["key"]
        # The plaintext key in the response must NOT be the hash
        assert re.fullmatch(r"kh_[0-9a-f]{32}", plaintext_in_response)
        # Verify hash is correct SHA-256 of plaintext
        expected_hash = hashlib.sha256(plaintext_in_response.encode()).hexdigest()
        # Hash should be 64-char hex (not the 35-char kh_ key)
        assert len(expected_hash) == 64
        assert expected_hash != plaintext_in_response

    def test_generate_api_key_prefix_stored(self):
        """AC7: key_prefix returned in response = plaintext[:8]."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        captured_prefix: list[str] = []

        async def _execute_side_effect(stmt, *args, **kwargs):
            sql = str(stmt)
            if "INSERT INTO api_keys" in sql and hasattr(stmt, "_bindparams"):
                bp = stmt._bindparams
                if "key_prefix" in bp:
                    v = bp["key_prefix"]
                    captured_prefix.append(v.value if hasattr(v, "value") else str(v))
            r = MagicMock()
            r.fetchone.return_value = ("row",)
            row = {
                "id": uuid.uuid4(),
                "key_prefix": captured_prefix[0] if captured_prefix else "kh_aaaabb",
                "name": None,
                "created_at": MagicMock(isoformat=lambda: "2026-04-21T00:00:00"),
            }
            inner = MagicMock()
            inner.__getitem__ = lambda self, k, _row=row: _row[k]
            r2 = MagicMock()
            r2.mappings.return_value.first.return_value = inner
            return r if "FROM users" in sql else r2

        db.execute = _execute_side_effect
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{target_user_id}/api-keys", json={})

        assert resp.status_code == 201
        key = resp.json()["key"]
        prefix = resp.json()["key_prefix"]
        # prefix must be first 8 chars of plaintext key
        assert prefix == key[:8]


class TestGenerateApiKeyUserNotFound:
    """S003/T003: AC2 — 404 NOT_FOUND when user missing."""

    def test_generate_api_key_user_not_found(self):
        """404 A005 shape when user_id does not exist."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{uuid.uuid4()}/api-keys", json={})

        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "message" in data["error"]
        assert "request_id" in data["error"]


class TestGenerateApiKeyNonAdmin:
    """S003/T003: AC9 — non-admin gets 403 FORBIDDEN (R003)."""

    def test_generate_api_key_non_admin(self):
        """403 when caller is not an admin."""
        user = _non_admin_user()
        db = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{uuid.uuid4()}/api-keys", json={})

        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# S004/T003: GET + DELETE /v1/admin/users/{user_id}/api-keys tests
# Spec: docs/user-management/spec/user-management.spec.md#S004
# ---------------------------------------------------------------------------

def _api_key_row(key_id: uuid.UUID | None = None) -> dict:
    kid = key_id or uuid.uuid4()
    return {
        "key_id": kid,
        "key_prefix": "kh_aabbcc",
        "name": "bot-key",
        "created_at": MagicMock(isoformat=lambda: "2026-04-21T00:00:00"),
    }


def _mappings_all_mock(rows: list[dict]) -> MagicMock:
    m = MagicMock()
    mock_rows = []
    for row in rows:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        r.get = lambda k, default=None, _row=row: _row.get(k, default)
        mock_rows.append(r)
    m.mappings.return_value.all.return_value = mock_rows
    return m


class TestListApiKeys:
    """S004/T003: GET /v1/admin/users/{user_id}/api-keys tests."""

    def test_list_api_keys_success(self):
        """AC1: 200 with items list; each item has key_id, key_prefix, name, created_at."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        key_id = uuid.uuid4()
        row = _api_key_row(key_id)

        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),       # user existence check
            _mappings_all_mock([row]),      # SELECT api_keys
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/v1/admin/users/{target_user_id}/api-keys")

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["key_id"] == str(key_id)
        assert item["key_prefix"] == "kh_aabbcc"
        assert item["name"] == "bot-key"
        assert "created_at" in item

    def test_list_api_keys_no_hash_in_response(self):
        """S005: key_hash must NOT appear in any item in the response."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        row = _api_key_row()

        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),
            _mappings_all_mock([row]),
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/v1/admin/users/{target_user_id}/api-keys")

        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert "key_hash" not in item, "key_hash must never appear in response (S005)"
            assert "key" not in item, "plaintext key must never appear in list response"

    def test_list_api_keys_empty(self):
        """AC: user with no keys returns empty items list."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),
            _mappings_all_mock([]),
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/v1/admin/users/{uuid.uuid4()}/api-keys")

        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_list_api_keys_user_not_found(self):
        """AC3: 404 NOT_FOUND A005 when user_id does not exist."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/v1/admin/users/{uuid.uuid4()}/api-keys")

        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "request_id" in data["error"]

    def test_list_api_keys_non_admin(self):
        """AC4: 403 FORBIDDEN for non-admin caller."""
        user = _non_admin_user()
        db = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/v1/admin/users/{uuid.uuid4()}/api-keys")

        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


class TestRevokeApiKey:
    """S004/T003: DELETE /v1/admin/users/{user_id}/api-keys/{key_id} tests."""

    def test_revoke_api_key_success(self):
        """AC5: 200 {"revoked": key_id} on successful revoke."""
        user = _admin_user()
        db = AsyncMock()
        target_user_id = uuid.uuid4()
        key_id = uuid.uuid4()

        # execute calls: user check, DELETE RETURNING id
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),   # user exists
            _fetchone_mock((key_id,)),  # DELETE RETURNING id
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{target_user_id}/api-keys/{key_id}")

        assert resp.status_code == 200
        assert resp.json()["revoked"] == str(key_id)
        db.commit.assert_called_once()

    def test_revoke_api_key_not_found(self):
        """AC6: 404 A005 when key_id does not exist for this user."""
        user = _admin_user()
        db = AsyncMock()

        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),   # user exists
            _fetchone_mock(None),       # DELETE RETURNING → no row
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            f"/v1/admin/users/{uuid.uuid4()}/api-keys/{uuid.uuid4()}"
        )

        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "request_id" in data["error"]

    def test_revoke_api_key_wrong_user(self):
        """AC7: 404 when key exists but belongs to different user (isolation)."""
        user = _admin_user()
        db = AsyncMock()
        # The WHERE clause includes user_id, so a key for a different user returns None
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),   # user_id exists
            _fetchone_mock(None),       # DELETE WHERE key_id AND user_id → no match
        ])

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            f"/v1/admin/users/{uuid.uuid4()}/api-keys/{uuid.uuid4()}"
        )

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_revoke_api_key_user_not_found(self):
        """AC3: 404 A005 when user_id does not exist."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            f"/v1/admin/users/{uuid.uuid4()}/api-keys/{uuid.uuid4()}"
        )

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_revoke_api_key_non_admin(self):
        """R003: 403 FORBIDDEN for non-admin caller."""
        user = _non_admin_user()
        db = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            f"/v1/admin/users/{uuid.uuid4()}/api-keys/{uuid.uuid4()}"
        )

        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"

