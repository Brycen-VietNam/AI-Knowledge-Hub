# Spec: docs/specs/auth-api-key-oidc.spec.md#S001
# Task: T005 — test_auth_models.py: User, ApiKey, AuditLog FK tests
# Uses SQLite in-memory — no live PostgreSQL required
# ⚠️ SQLite caveat: ARRAY(INTEGER) unsupported — api_keys table skipped in DDL;
#    ApiKey column/structure tests use ORM class inspection only.
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.models.base import Base
from backend.db.models.user import User
from backend.db.models.audit_log import AuditLog
from backend.db.models.api_key import ApiKey
from backend.db.models.document import Document
from backend.db.models.user_group import UserGroup


@pytest.fixture(scope="module")
def engine():
    """SQLite in-memory engine. api_keys table skipped (ARRAY not supported)."""
    eng = create_engine("sqlite:///:memory:")
    # Create all tables except api_keys (PostgreSQL ARRAY type unsupported in SQLite)
    tables_to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name != "api_keys"
    ]
    Base.metadata.create_all(eng, tables=tables_to_create)
    yield eng
    Base.metadata.drop_all(eng, tables=tables_to_create)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


# --- Table name checks ---

def test_user_tablename():
    assert User.__tablename__ == "users"


def test_api_key_tablename():
    assert ApiKey.__tablename__ == "api_keys"


# --- Column structure checks ---

def test_api_key_no_plaintext():
    """key_plaintext must NOT be a column — hash-only by design (R002)."""
    col_names = [c.key for c in ApiKey.__table__.columns]
    assert "key_plaintext" not in col_names
    assert "key_hash" in col_names


# --- FK checks ---

def test_audit_log_fk_to_users(engine):
    """audit_logs.user_id must have FK to users(id) — upgraded from TEXT placeholder."""
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("audit_logs")
    targets = [(fk["referred_table"], fk["referred_columns"]) for fk in fks]
    assert ("users", ["id"]) in targets


# --- Roundtrip tests ---

def test_user_sub_unique(session):
    """Two users with the same sub must raise IntegrityError."""
    sub = f"keycloak|unique-test-{uuid.uuid4()}"
    u1 = User(sub=sub, email="a@example.com")
    u2 = User(sub=sub, email="b@example.com")
    session.add(u1)
    session.flush()
    session.add(u2)
    with pytest.raises(IntegrityError):
        session.flush()


def test_audit_log_user_id_is_uuid(session):
    """AuditLog.user_id must accept UUID (not TEXT) after T004 migration."""
    group = UserGroup(name="Auth-Test-Group")
    session.add(group)
    session.flush()

    doc = Document(id=uuid.uuid4(), title="Auth Test Doc", lang="en", user_group_id=group.id)
    session.add(doc)
    session.flush()

    user = User(sub=f"keycloak|{uuid.uuid4()}", email="test@example.com")
    session.add(user)
    session.flush()

    log = AuditLog(
        id=uuid.uuid4(),
        user_id=user.id,
        doc_id=doc.id,
        query_hash="sha256:abc123",
    )
    session.add(log)
    session.flush()
    assert isinstance(log.user_id, uuid.UUID)
    assert log.user_id == user.id


# --- __init__ export check ---

def test_user_token_version_defaults_to_1(session):
    """S002/T002: token_version defaults to 1 when not provided."""
    u = User(sub=f"test|{uuid.uuid4()}", email=None)
    session.add(u)
    session.flush()
    assert u.token_version == 1


def test_user_token_version_custom_value(session):
    """S002/T002: token_version stores custom integer value."""
    u = User(sub=f"test|{uuid.uuid4()}", email=None, token_version=5)
    session.add(u)
    session.flush()
    assert u.token_version == 5


def test_models_init_exports_auth():
    """User and ApiKey must be importable from backend.db.models package."""
    from backend.db.models import User as U
    from backend.db.models import ApiKey as AK
    assert U.__tablename__ == "users"
    assert AK.__tablename__ == "api_keys"
