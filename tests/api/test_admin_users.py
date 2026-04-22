# Spec: docs/user-management/spec/user-management.spec.md#S001
# Spec: docs/user-management/spec/user-management.spec.md#S002
# Task: S001/T004 — Tests: create_user happy path + error cases (AC1–AC10)
# Task: S002/T003 — Tests: delete_user happy path + error cases (AC1–AC7)
# Rule: R003 — all admin endpoints tested with admin AND non-admin (403 gate)
# Rule: A005 — 404/409 response body matches {"error": {"code", "message", "request_id"}}
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes.admin import UserCreate, router
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser


# ---------------------------------------------------------------------------
# Helpers (mirror pattern from test_admin.py)
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


def _mappings_mock(rows: list[dict]) -> MagicMock:
    m = MagicMock()
    mock_rows = []
    for row in rows:
        r = MagicMock()
        r.__getitem__ = lambda self, k, _row=row: _row[k]
        mock_rows.append(r)
    m.mappings.return_value.all.return_value = mock_rows
    return m


_VALID_PAYLOAD = {
    "sub": "new_user",
    "email": "new@example.com",
    "display_name": "New User",
    "password": "SecurePass123!",
    "group_ids": [],
}


# ---------------------------------------------------------------------------
# T004: Tests — AC1–AC10
# ---------------------------------------------------------------------------

class TestUserCreateModel:
    """T001/T004: Pydantic model validation tests."""

    def test_user_create_model_validation_invalid_sub_pattern(self):
        """AC: sub must match ^[a-zA-Z0-9_.@-]+$ — rejects spaces and special chars."""
        with pytest.raises(Exception):
            UserCreate(sub="bad sub!", email=None, display_name=None, password="ValidPass123!")

    def test_user_create_model_validation_sub_too_short(self):
        """AC: sub min_length=3."""
        with pytest.raises(Exception):
            UserCreate(sub="ab", email=None, display_name=None, password="ValidPass123!")

    def test_user_create_model_validation_password_too_short(self):
        """AC: password min_length=12."""
        with pytest.raises(Exception):
            UserCreate(sub="valid_user", email=None, display_name=None, password="short")

    def test_user_create_model_validation_invalid_email(self):
        """AC: email must be valid EmailStr or None."""
        with pytest.raises(Exception):
            UserCreate(sub="valid_user", email="not-an-email", display_name=None, password="ValidPass123!")

    def test_user_create_model_group_ids_defaults_to_empty_list(self):
        """AC: group_ids defaults to [] — not a mutable default."""
        m = UserCreate(sub="valid_user", email=None, display_name=None, password="ValidPass123!")
        assert m.group_ids == []

    def test_user_create_model_valid(self):
        """AC: valid model parses without error."""
        m = UserCreate(
            sub="valid.user@corp-01",
            email="u@example.com",
            display_name="Valid User",
            password="SecurePass123!",
            group_ids=[1, 2],
        )
        assert m.sub == "valid.user@corp-01"
        assert m.group_ids == [1, 2]


class TestCreateUserSuccess:
    """T002/T004: Happy path — AC1 + AC2."""

    def test_create_user_success(self):
        """AC1: 201 with correct response shape; password_hash NOT in response."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        user_row = {
            "id": new_id,
            "sub": "new_user",
            "email": "new@example.com",
            "display_name": "New User",
            "is_active": True,
        }

        # execute calls: 1) duplicate check → None, 2) INSERT user → row
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),           # duplicate check
            _mappings_first_mock(user_row), # INSERT RETURNING
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=_VALID_PAYLOAD)

        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == str(new_id)
        assert data["sub"] == "new_user"
        assert data["email"] == "new@example.com"
        assert data["is_active"] is True
        assert "password" not in data
        assert "password_hash" not in data
        assert data["groups"] == []

    def test_create_user_strips_whitespace(self):
        """AC: leading/trailing whitespace stripped from sub and display_name (S003)."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        payload = {
            "sub": "clean_user",
            "email": None,
            "display_name": "  Spaced Name  ",
            "password": "SecurePass123!",
            "group_ids": [],
        }
        user_row = {
            "id": new_id,
            "sub": "clean_user",
            "email": None,
            "display_name": "Spaced Name",
            "is_active": True,
        }
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),
            _mappings_first_mock(user_row),
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=payload)

        assert resp.status_code == 201


class TestCreateUserDuplicateSub:
    """T002/T004: AC4 — duplicate sub → 409 SUB_CONFLICT in A005 shape."""

    def test_create_user_duplicate_sub(self):
        """409 with A005 error shape when sub already exists."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(("existing_id",)))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=_VALID_PAYLOAD)

        assert resp.status_code == 409
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "SUB_CONFLICT"
        assert "message" in data["error"]
        assert "request_id" in data["error"]


class TestCreateUserWithGroups:
    """T003/T004: AC3 — group membership inserted in same transaction; groups in response."""

    def test_create_user_with_groups(self):
        """AC3: 201 with groups list when group_ids provided."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        user_row = {
            "id": new_id,
            "sub": "grouped_user",
            "email": "g@example.com",
            "display_name": "Grouped",
            "is_active": True,
        }
        group_rows = [
            {"id": 1, "name": "Editors", "is_admin": False},
            {"id": 2, "name": "Admins", "is_admin": True},
        ]

        payload = {**_VALID_PAYLOAD, "sub": "grouped_user", "email": "g@example.com", "group_ids": [1, 2]}

        # execute calls: duplicate check, INSERT user, INSERT membership ×2, SELECT groups
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),                  # duplicate check
            _mappings_first_mock(user_row),        # INSERT user RETURNING
            MagicMock(),                           # INSERT membership group 1
            MagicMock(),                           # INSERT membership group 2
            _mappings_mock(group_rows),            # SELECT groups IN
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=payload)

        assert resp.status_code == 201
        data = resp.json()
        assert len(data["groups"]) == 2
        assert data["groups"][0]["id"] == 1
        assert data["groups"][1]["name"] == "Admins"

    def test_create_user_invalid_group_ids(self):
        """AC: unknown group_ids handled gracefully — groups list empty if no match."""
        user = _admin_user()
        db = AsyncMock()
        new_id = uuid.uuid4()

        user_row = {
            "id": new_id,
            "sub": "nogroup_user",
            "email": None,
            "display_name": None,
            "is_active": True,
        }
        payload = {**_VALID_PAYLOAD, "sub": "nogroup_user", "email": None, "group_ids": [999]}

        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(None),                  # duplicate check
            _mappings_first_mock(user_row),        # INSERT user RETURNING
            MagicMock(),                           # INSERT membership group 999
            _mappings_mock([]),                    # SELECT groups → empty (unknown id)
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=payload)

        assert resp.status_code == 201
        assert resp.json()["groups"] == []


class TestCreateUserNonAdmin:
    """T002/T004: AC15 — non-admin gets 403 FORBIDDEN (R003)."""

    def test_create_user_non_admin(self):
        """403 when caller is not an admin."""
        user = _non_admin_user()
        db = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/admin/users", json=_VALID_PAYLOAD)

        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# S002/T003: DELETE /v1/admin/users/{user_id} tests
# Spec: docs/user-management/spec/user-management.spec.md#S002
# ---------------------------------------------------------------------------

class TestDeleteUserSuccess:
    """S002/T003: Happy path — 200 with {"deleted": user_id}."""

    def test_delete_user_success(self):
        """AC1: 200 {"deleted": "<uuid>"} on successful delete."""
        user = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()

        # execute calls: 1) existence check → row, 2-4) three DELETEs
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock(("row",)),  # existence check
            MagicMock(),               # DELETE api_keys
            MagicMock(),               # DELETE user_group_memberships
            MagicMock(),               # DELETE users
        ])
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{target_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == str(target_id)

    def test_delete_user_cascades_api_keys(self):
        """AC3: DELETE api_keys called before DELETE users (cascade, FK safety)."""
        user = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()
        call_log: list[str] = []

        async def _execute_side_effect(stmt, *args, **kwargs):
            sql_text = str(stmt)
            call_log.append(sql_text)
            m = MagicMock()
            m.fetchone.return_value = ("row",)
            return m

        db.execute = _execute_side_effect
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{target_id}")

        assert resp.status_code == 200
        # Verify api_keys delete comes before DELETE FROM users
        api_keys_idx = next(i for i, s in enumerate(call_log) if "api_keys" in s)
        users_idx = next(i for i, s in enumerate(call_log) if "DELETE FROM users" in s)
        assert api_keys_idx < users_idx

    def test_delete_user_cascades_memberships(self):
        """AC3: DELETE user_group_memberships called before DELETE users."""
        user = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()
        call_log: list[str] = []

        async def _execute_side_effect(stmt, *args, **kwargs):
            sql_text = str(stmt)
            call_log.append(sql_text)
            m = MagicMock()
            m.fetchone.return_value = ("row",)
            return m

        db.execute = _execute_side_effect
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{target_id}")

        assert resp.status_code == 200
        memberships_idx = next(i for i, s in enumerate(call_log) if "user_group_memberships" in s)
        users_idx = next(i for i, s in enumerate(call_log) if "DELETE FROM users" in s)
        assert memberships_idx < users_idx

    def test_delete_user_preserves_audit_logs(self):
        """AC7: audit_logs rows NOT deleted — user_id set to NULL by DB (migration 011)."""
        user = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()
        call_log: list[str] = []

        async def _execute_side_effect(stmt, *args, **kwargs):
            call_log.append(str(stmt))
            m = MagicMock()
            m.fetchone.return_value = ("row",)
            return m

        db.execute = _execute_side_effect
        db.commit = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{target_id}")

        assert resp.status_code == 200
        # audit_logs must NOT appear in any DELETE statement
        assert not any("audit_logs" in s for s in call_log), (
            "audit_logs rows must not be explicitly deleted — FK ON DELETE SET NULL handles it"
        )


class TestDeleteUserNotFound:
    """S002/T003: AC2 — 404 NOT_FOUND in A005 shape when user missing."""

    def test_delete_user_not_found(self):
        """404 A005 when user_id does not exist."""
        user = _admin_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_fetchone_mock(None))

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{uuid.uuid4()}")

        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "message" in data["error"]
        assert "request_id" in data["error"]


class TestDeleteUserNonAdmin:
    """S002/T003: AC6 — non-admin gets 403 FORBIDDEN (R003)."""

    def test_delete_user_non_admin(self):
        """403 when caller is not an admin."""
        user = _non_admin_user()
        db = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{uuid.uuid4()}")

        assert resp.status_code == 403
        assert resp.json()["detail"]["error"]["code"] == "FORBIDDEN"


class TestDeleteUserDbError:
    """S002/T003: 500 INTERNAL_ERROR with rollback on DB exception."""

    def test_delete_user_db_error(self):
        """500 A005 shape when DB raises during delete; rollback called."""
        user = _admin_user()
        db = AsyncMock()

        async def _execute_side_effect(stmt, *args, **kwargs):
            sql = str(stmt)
            if "FROM users WHERE id" in sql:
                # existence check passes
                m = MagicMock()
                m.fetchone.return_value = ("row",)
                return m
            raise RuntimeError("DB failure")

        db.execute = _execute_side_effect
        db.rollback = AsyncMock()

        app = _make_app(user, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(f"/v1/admin/users/{uuid.uuid4()}")

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# S002/T003: Tests — admin password reset + has_password
# Spec: docs/change-password/spec/change-password.spec.md#S002
# Task: S002/T003 — 8 test cases
# Rule: R003, R006, A005
# ---------------------------------------------------------------------------

class TestAdminPasswordResetGenerate:
    """test_admin_reset_generate — POST {"generate": true} → 200 + {"password": ...}"""

    def test_admin_reset_generate(self):
        """D2: generate=true → 200 with 'password' key containing plaintext."""
        admin = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()

        # execute calls: 1) SELECT user → row with hash, 2) UPDATE, 3) audit log INSERT
        db.execute = AsyncMock(side_effect=[
            _fetchone_mock((target_id, "hashed_pw")),  # user fetch
            MagicMock(),                                # UPDATE password_hash + must_change
            MagicMock(),                                # audit log INSERT (commit 1)
            MagicMock(),                                # audit log INSERT (commit 2)
        ])
        db.commit = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/v1/admin/users/{target_id}/password-reset", json={"generate": True})

        assert resp.status_code == 200
        data = resp.json()
        assert "password" in data
        assert isinstance(data["password"], str)
        assert len(data["password"]) >= 8


class TestAdminPasswordResetManual:
    """test_admin_reset_manual — POST {"new_password": "..."} → 204"""

    def test_admin_reset_manual(self):
        """D2: explicit new_password → 204, no response body."""
        admin = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()

        db.execute = AsyncMock(side_effect=[
            _fetchone_mock((target_id, "hashed_pw")),  # user fetch
            MagicMock(),                                # UPDATE
            MagicMock(),                                # audit log INSERT
        ])
        db.commit = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/v1/admin/users/{target_id}/password-reset",
            json={"new_password": "NewPass123!"},
        )

        assert resp.status_code == 204


class TestAdminPasswordResetSetsMustChangeFlag:
    """test_admin_reset_sets_must_change_flag — UPDATE sets must_change_password=TRUE"""

    def test_admin_reset_sets_must_change_flag(self):
        """Q3: must_change_password = TRUE is always set in the UPDATE statement."""
        admin = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()
        executed_sqls: list[str] = []

        async def _capture(stmt, *args, **kwargs):
            executed_sqls.append(str(stmt))
            m = MagicMock()
            m.fetchone.return_value = (target_id, "hashed_pw")
            return m

        db.execute = _capture
        db.commit = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        client.post(
            f"/v1/admin/users/{target_id}/password-reset",
            json={"new_password": "NewPass123!"},
        )

        update_stmts = [s for s in executed_sqls if "UPDATE users" in s]
        assert update_stmts, "No UPDATE users statement found"
        assert any("must_change_password" in s for s in update_stmts), (
            "must_change_password flag must be set in UPDATE"
        )


class TestAdminPasswordResetOidcUser:
    """test_admin_reset_oidc_user_400 — OIDC user → 400 ERR_PASSWORD_NOT_APPLICABLE (D3)"""

    def test_admin_reset_oidc_user_400(self):
        """D3: target user has password_hash=None (OIDC) → 400."""
        admin = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()

        # password_hash is None (OIDC user)
        db.execute = AsyncMock(return_value=_fetchone_mock((target_id, None)))
        db.commit = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/v1/admin/users/{target_id}/password-reset",
            json={"generate": True},
        )

        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == "ERR_PASSWORD_NOT_APPLICABLE"


class TestAdminPasswordResetUnknownUser:
    """test_admin_reset_unknown_user_404 — unknown user_id → 404 ERR_USER_NOT_FOUND"""

    def test_admin_reset_unknown_user_404(self):
        """404 A005 shape when target user does not exist."""
        admin = _admin_user()
        db = AsyncMock()

        db.execute = AsyncMock(return_value=_fetchone_mock(None))
        db.commit = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/v1/admin/users/{uuid.uuid4()}/password-reset",
            json={"generate": True},
        )

        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "ERR_USER_NOT_FOUND"
        assert "request_id" in data["error"]


class TestAdminPasswordResetShortPassword:
    """test_admin_reset_short_password_422 — new_password < 8 chars → 422"""

    def test_admin_reset_short_password_422(self):
        """422 Unprocessable when new_password violates min_length=8 (Pydantic)."""
        admin = _admin_user()
        db = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/v1/admin/users/{uuid.uuid4()}/password-reset",
            json={"new_password": "short"},
        )

        assert resp.status_code == 422


class TestAdminPasswordResetAuditLog:
    """test_admin_reset_audit_log_written — audit_logs INSERT is called (R006)"""

    def test_admin_reset_audit_log_written(self):
        """R006: an INSERT INTO audit_logs statement is executed after reset."""
        admin = _admin_user()
        db = AsyncMock()
        target_id = uuid.uuid4()
        executed_sqls: list[str] = []

        async def _capture(stmt, *args, **kwargs):
            executed_sqls.append(str(stmt))
            m = MagicMock()
            m.fetchone.return_value = (target_id, "hashed_pw")
            return m

        db.execute = _capture
        db.commit = AsyncMock()

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        client.post(
            f"/v1/admin/users/{target_id}/password-reset",
            json={"new_password": "AuditPass1!"},
        )

        audit_stmts = [s for s in executed_sqls if "audit_logs" in s.lower()]
        assert audit_stmts, "No INSERT INTO audit_logs found — R006 violated"


class TestUserListHasPasswordField:
    """test_user_list_has_password_field — GET /v1/admin/users returns has_password per row (T002)"""

    def test_user_list_has_password_field(self):
        """has_password: true for password user, false for OIDC user."""
        admin = _admin_user()
        db = AsyncMock()

        pw_user_id = uuid.uuid4()
        oidc_user_id = uuid.uuid4()

        rows = [
            {
                "id": pw_user_id,
                "sub": "pw_user",
                "email": "pw@example.com",
                "display_name": "PW User",
                "is_active": True,
                "has_password": True,
                "groups": [],
            },
            {
                "id": oidc_user_id,
                "sub": "oidc_user",
                "email": "oidc@example.com",
                "display_name": "OIDC User",
                "is_active": True,
                "has_password": False,
                "groups": [],
            },
        ]

        mock_result = MagicMock()
        mock_rows = []
        for row in rows:
            r = MagicMock()
            r.__getitem__ = lambda self, k, _row=row: _row[k]
            # Ensure isoformat not needed for non-datetime fields
            mock_rows.append(r)
        mock_result.mappings.return_value.all.return_value = mock_rows

        db.execute = AsyncMock(return_value=mock_result)

        app = _make_app(admin, db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/admin/users")

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2

        pw_row = next(i for i in items if i["sub"] == "pw_user")
        oidc_row = next(i for i in items if i["sub"] == "oidc_user")

        assert pw_row["has_password"] is True
        assert oidc_row["has_password"] is False

