# Spec: docs/specs/db-schema-embeddings.spec.md#S001
# Task: T002b — Unit tests for ORM models
# Uses SQLite in-memory — no live PostgreSQL required
import uuid

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.db.models.base import Base
from backend.db.models.user_group import UserGroup
from backend.db.models.document import Document
from backend.db.models.embedding import Embedding
from backend.db.models.audit_log import AuditLog


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


# --- Table name checks ---

def test_user_group_tablename():
    assert UserGroup.__tablename__ == "user_groups"


def test_document_tablename():
    assert Document.__tablename__ == "documents"


def test_embedding_tablename():
    assert Embedding.__tablename__ == "embeddings"


def test_audit_log_tablename():
    assert AuditLog.__tablename__ == "audit_logs"


# --- Column presence checks ---

def test_embeddings_has_no_vector_column(engine):
    """embedding vector(1024) must NOT exist here — added in S002 migration."""
    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("embeddings")]
    assert "embedding" not in cols


def test_documents_has_no_content_fts_column(engine):
    """content_fts tsvector must NOT exist here — added in S003 migration."""
    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("documents")]
    assert "content_fts" not in cols


def test_embeddings_has_user_group_id(engine):
    """user_group_id must exist on embeddings for RBAC WHERE clause (R001)."""
    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("embeddings")]
    assert "user_group_id" in cols


# --- FK relationship checks ---

def test_document_fk_to_user_groups(engine):
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("documents")
    targets = [(fk["referred_table"], fk["referred_columns"]) for fk in fks]
    assert ("user_groups", ["id"]) in targets


def test_embedding_fk_to_documents(engine):
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("embeddings")
    targets = [(fk["referred_table"], fk["referred_columns"]) for fk in fks]
    assert ("documents", ["id"]) in targets


def test_audit_log_fk_to_documents(engine):
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("audit_logs")
    targets = [(fk["referred_table"], fk["referred_columns"]) for fk in fks]
    assert ("documents", ["id"]) in targets


# --- Basic roundtrip (insert + query) ---

def test_user_group_insert(session):
    group = UserGroup(name="Engineering")
    session.add(group)
    session.flush()
    assert group.id is not None
    assert group.name == "Engineering"


def test_document_insert(session):
    group = UserGroup(name="HR")
    session.add(group)
    session.flush()

    doc = Document(
        id=uuid.uuid4(),
        title="Test Doc",
        lang="en",
        user_group_id=group.id,
    )
    session.add(doc)
    session.flush()
    assert doc.id is not None
    assert doc.lang == "en"


def test_audit_log_user_id_is_text(session):
    """user_id must accept any text string (placeholder, no FK constraint)."""
    group = UserGroup(name="Ops")
    session.add(group)
    session.flush()

    doc = Document(id=uuid.uuid4(), title="Ops Doc", lang="ja", user_group_id=group.id)
    session.add(doc)
    session.flush()

    log = AuditLog(
        id=uuid.uuid4(),
        user_id="auth0|some-user-id-placeholder",
        doc_id=doc.id,
        query_hash="abc123",
    )
    session.add(log)
    session.flush()
    assert log.user_id == "auth0|some-user-id-placeholder"


# --- __init__ export check (T003) ---

def test_models_init_exports():
    """All 4 models + Base must be importable from backend.db.models package."""
    from backend.db.models import Base as B
    from backend.db.models import UserGroup as UG
    from backend.db.models import Document as Doc
    from backend.db.models import Embedding as Emb
    from backend.db.models import AuditLog as AL
    assert B is not None
    assert UG.__tablename__ == "user_groups"
    assert Doc.__tablename__ == "documents"
    assert Emb.__tablename__ == "embeddings"
    assert AL.__tablename__ == "audit_logs"
