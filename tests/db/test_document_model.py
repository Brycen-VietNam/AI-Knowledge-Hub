# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S005
# Task: S005-db-T002 — Document.status + Embedding.text ORM field tests
# Decision: D07 — status lifecycle: processing → ready | failed
# Decision: D11 — chunk text stored in embeddings.text, not documents
import uuid

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.db.models.base import Base
from backend.db.models.document import Document
from backend.db.models.embedding import Embedding
from backend.db.models.user_group import UserGroup


@pytest.fixture(scope="module")
def engine():
    tables = [t for t in Base.metadata.sorted_tables if t.name != "api_keys"]
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng, tables=tables)
    yield eng
    Base.metadata.drop_all(eng, tables=tables)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


@pytest.fixture
def group(session):
    g = UserGroup(name="TestGroup")
    session.add(g)
    session.flush()
    return g


@pytest.fixture
def doc(session, group):
    d = Document(id=uuid.uuid4(), title="Test", lang="en", user_group_id=group.id)
    session.add(d)
    session.flush()
    return d


# --- Document.status ---

def test_document_status_column_exists(engine):
    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("documents")]
    assert "status" in cols


def test_document_status_default_is_processing(session, group):
    """D07: Document without explicit status defaults to 'processing'."""
    doc = Document(id=uuid.uuid4(), title="No Status", lang="en", user_group_id=group.id)
    session.add(doc)
    session.flush()
    assert doc.status == "processing"


def test_document_status_accepts_ready(session, group):
    doc = Document(id=uuid.uuid4(), title="Ready Doc", lang="ja", user_group_id=group.id, status="ready")
    session.add(doc)
    session.flush()
    assert doc.status == "ready"


def test_document_status_accepts_failed(session, group):
    doc = Document(id=uuid.uuid4(), title="Failed Doc", lang="vi", user_group_id=group.id, status="failed")
    session.add(doc)
    session.flush()
    assert doc.status == "failed"


def test_document_status_can_be_updated(session, doc):
    doc.status = "ready"
    session.flush()
    session.refresh(doc)
    assert doc.status == "ready"


# --- Embedding.text ---

def test_embedding_text_column_exists(engine):
    """D11: embeddings.text column must exist for chunk text storage."""
    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("embeddings")]
    assert "text" in cols


def test_embedding_stores_chunk_text(session, doc):
    """D11: chunk text stored in Embedding.text, retrievable for RAG."""
    emb = Embedding(
        id=uuid.uuid4(),
        doc_id=doc.id,
        chunk_index=0,
        lang="en",
        text="This is the first chunk of the document.",
    )
    session.add(emb)
    session.flush()
    session.refresh(emb)
    assert emb.text == "This is the first chunk of the document."


def test_embedding_text_is_not_nullable(engine):
    """D11: embeddings.text must be NOT NULL."""
    inspector = inspect(engine)
    cols = {c["name"]: c for c in inspector.get_columns("embeddings")}
    assert cols["text"]["nullable"] is False


def test_embedding_multiple_chunks_preserve_order(session, doc):
    chunks = ["First chunk.", "Second chunk.", "Third chunk."]
    for i, text in enumerate(chunks):
        session.add(Embedding(
            id=uuid.uuid4(), doc_id=doc.id, chunk_index=i, lang="en", text=text,
        ))
    session.flush()
    results = (
        session.query(Embedding)
        .filter_by(doc_id=doc.id)
        .order_by(Embedding.chunk_index)
        .all()
    )
    assert [r.text for r in results] == chunks
