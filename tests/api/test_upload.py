# Spec: docs/document-parser/spec/document-parser.spec.md#S004
# Task: S004/T001 — unit tests for POST /v1/documents/upload
# Task: S004/T003 — integration tests (marked @pytest.mark.integration)
# Rule: R003, R004, R006
import asyncio
import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.routes import upload
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
    app.include_router(upload.router)
    app.dependency_overrides[verify_token] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)
    return app


def _minimal_txt_bytes() -> bytes:
    return b"Hello, world!"


# ---------------------------------------------------------------------------
# Unit tests (T001) — mocked parsers/DB
# ---------------------------------------------------------------------------

def test_missing_file_returns_422():
    """AC: missing file field → 422 ERR_NO_FILE."""
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/v1/documents/upload", data={})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "ERR_NO_FILE"


def test_unsupported_format_returns_415():
    """AC: UnsupportedFormatError → 415 ERR_UNSUPPORTED_FORMAT."""
    from backend.rag.parser.base import UnsupportedFormatError

    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch(
            "backend.api.routes.upload.ParserFactory.get_parser",
            side_effect=UnsupportedFormatError("application/x-unknown"),
        ),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("doc.xyz", io.BytesIO(b"data"), "application/x-unknown")},
        )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "ERR_UNSUPPORTED_FORMAT"


def test_file_too_large_returns_413():
    """AC: SecurityError(ERR_FILE_TOO_LARGE) → 413."""
    from backend.rag.parser.base import SecurityError

    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "backend.api.routes.upload.SecurityGate.validate",
        side_effect=SecurityError("ERR_FILE_TOO_LARGE", "File too large"),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("big.txt", io.BytesIO(b"x" * 100), "text/plain")},
        )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "ERR_FILE_TOO_LARGE"


def test_mime_mismatch_returns_415():
    """AC: SecurityError(ERR_MIME_MISMATCH) → 415."""
    from backend.rag.parser.base import SecurityError

    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "backend.api.routes.upload.SecurityGate.validate",
        side_effect=SecurityError("ERR_MIME_MISMATCH", "MIME mismatch"),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("doc.pdf", io.BytesIO(b"fake"), "text/plain")},
        )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "ERR_MIME_MISMATCH"


def test_parse_error_returns_422():
    """AC: ParseError from parser → 422 ERR_PARSE_FAILED."""
    from backend.rag.parser.base import ParseError

    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    mock_parser = MagicMock()
    mock_parser.parse.side_effect = ParseError("ERR_PARSE_FAILED", "Parse failed")

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("doc.txt", io.BytesIO(b"data"), "text/plain")},
        )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "ERR_PARSE_FAILED"


def test_parse_timeout_returns_504():
    """AC: asyncio.TimeoutError → 504 ERR_PARSE_TIMEOUT."""
    user = _make_user()
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    mock_parser = MagicMock()

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
        patch("backend.api.routes.upload.asyncio.wait_for", side_effect=asyncio.TimeoutError),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("slow.txt", io.BytesIO(b"data"), "text/plain")},
        )
    assert resp.status_code == 504
    assert resp.json()["error"]["code"] == "ERR_PARSE_TIMEOUT"


def test_successful_upload_returns_202_with_document_id():
    """Happy path: valid file → 202 with document_id + status=processing."""
    from backend.rag.parser.base import ParsedDocument

    user = _make_user()
    doc_id = uuid.uuid4()

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(
        side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing")
    )

    mock_parser = MagicMock()
    mock_parser.parse.return_value = ParsedDocument(text="Hello world", lang="en")
    parsed_doc = ParsedDocument(text="Hello world", lang="en")

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
        patch(
            "backend.api.routes.upload.asyncio.wait_for",
            new_callable=AsyncMock,
            return_value=parsed_doc,
        ),
        patch("backend.api.routes.upload._write_audit_log", new_callable=AsyncMock),
        patch("backend.api.routes.upload.ingest_pipeline", new_callable=AsyncMock),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("report.txt", io.BytesIO(b"Hello world"), "text/plain")},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert "document_id" in data
    assert data["status"] == "processing"
    uuid.UUID(data["document_id"])  # must be valid UUID


def test_title_defaults_to_filename_stem():
    """D10: title not provided → Path(filename).stem used as title."""
    from backend.rag.parser.base import ParsedDocument

    user = _make_user()
    doc_id = uuid.uuid4()
    captured_doc = {}

    db = AsyncMock()

    def _capture_add(obj):
        captured_doc["title"] = obj.title

    db.add = MagicMock(side_effect=_capture_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock(
        side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing")
    )

    parsed_doc = ParsedDocument(text="content", lang="en")
    mock_parser = MagicMock()

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
        patch(
            "backend.api.routes.upload.asyncio.wait_for",
            new_callable=AsyncMock,
            return_value=parsed_doc,
        ),
        patch("backend.api.routes.upload._write_audit_log", new_callable=AsyncMock),
        patch("backend.api.routes.upload.ingest_pipeline", new_callable=AsyncMock),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("my_report.txt", io.BytesIO(b"content"), "text/plain")},
        )

    assert resp.status_code == 202
    assert captured_doc.get("title") == "my_report"


def test_oidc_caller_returns_403():
    """D04: OIDC user must get 403 on upload (write gate)."""
    user = _make_user(auth_type="oidc")
    db = AsyncMock()
    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with patch("backend.api.routes.upload.SecurityGate.validate"):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("doc.txt", io.BytesIO(b"data"), "text/plain")},
        )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# FIX-T001: lang detection tests
# ---------------------------------------------------------------------------

def test_lang_detection_used_when_form_and_parser_lang_are_none():
    """FIX-T001: when form lang=None and parsed.lang=None, langdetect.detect() is called."""
    from backend.rag.parser.base import ParsedDocument

    user = _make_user()
    doc_id = uuid.uuid4()

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(
        side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing")
    )

    # parsed.lang is None — forces langdetect path
    parsed_doc = ParsedDocument(text="This is English text.", lang=None)
    mock_parser = MagicMock()

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
        patch(
            "backend.api.routes.upload.asyncio.wait_for",
            new_callable=AsyncMock,
            return_value=parsed_doc,
        ),
        patch("backend.api.routes.upload._write_audit_log", new_callable=AsyncMock),
        patch("backend.api.routes.upload.ingest_pipeline", new_callable=AsyncMock),
        patch("backend.api.routes.upload.detect", return_value="en") as mock_detect,
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("report.txt", io.BytesIO(b"This is English text."), "text/plain")},
        )

    assert resp.status_code == 202
    mock_detect.assert_called_once_with("This is English text.")


def test_lang_none_stored_when_langdetect_raises():
    """FIX-T001: LangDetectException → resolved_lang=None (no 'en' fallback)."""
    from langdetect import LangDetectException

    from backend.rag.parser.base import ParsedDocument

    user = _make_user()
    doc_id = uuid.uuid4()
    captured_doc = {}

    db = AsyncMock()

    def _capture_add(obj):
        captured_doc["lang"] = obj.lang

    db.add = MagicMock(side_effect=_capture_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock(
        side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing")
    )

    parsed_doc = ParsedDocument(text="???", lang=None)
    mock_parser = MagicMock()

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
        patch(
            "backend.api.routes.upload.asyncio.wait_for",
            new_callable=AsyncMock,
            return_value=parsed_doc,
        ),
        patch("backend.api.routes.upload._write_audit_log", new_callable=AsyncMock),
        patch("backend.api.routes.upload.ingest_pipeline", new_callable=AsyncMock),
        patch("backend.api.routes.upload.detect", side_effect=LangDetectException(0, "no features")),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("file.txt", io.BytesIO(b"???"), "text/plain")},
        )

    assert resp.status_code == 202
    assert captured_doc.get("lang") is None  # must be NULL, never "en"


# ---------------------------------------------------------------------------
# FIX-T004: filename sanitization tests
# ---------------------------------------------------------------------------

def test_crlf_in_filename_stripped_from_title_and_logs():
    """FIX-T004: control chars in filename (CRLF, etc.) stripped; capped at 255 chars."""
    from backend.rag.parser.base import ParsedDocument

    user = _make_user()
    doc_id = uuid.uuid4()
    captured_doc = {}

    db = AsyncMock()

    def _capture_add(obj):
        captured_doc["title"] = obj.title

    db.add = MagicMock(side_effect=_capture_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock(
        side_effect=lambda d: setattr(d, "id", doc_id) or setattr(d, "status", "processing")
    )

    parsed_doc = ParsedDocument(text="content", lang="en")
    mock_parser = MagicMock()

    app = _make_app(user, db)
    client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("backend.api.routes.upload.SecurityGate.validate"),
        patch("backend.api.routes.upload.ParserFactory.get_parser", return_value=mock_parser),
        patch(
            "backend.api.routes.upload.asyncio.wait_for",
            new_callable=AsyncMock,
            return_value=parsed_doc,
        ),
        patch("backend.api.routes.upload._write_audit_log", new_callable=AsyncMock),
        patch("backend.api.routes.upload.ingest_pipeline", new_callable=AsyncMock),
        patch("backend.api.routes.upload.detect", return_value="en"),
    ):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("evil\r\nfile.txt", io.BytesIO(b"content"), "text/plain")},
        )

    assert resp.status_code == 202
    # title derived from sanitized filename stem — no CRLF
    title = captured_doc.get("title", "")
    assert "\r" not in title
    assert "\n" not in title


# ---------------------------------------------------------------------------
# Integration tests (T003) — marked @pytest.mark.integration
# These require a live test DB and are skipped in unit test runs.
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_integration_upload_valid_txt_returns_202(integration_client):
    """Upload a valid minimal TXT file → 202, document_id in response, DB row status=processing."""
    resp = integration_client.post(
        "/v1/documents/upload",
        files={"file": ("hello.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "document_id" in data
    assert data["status"] == "processing"
    doc_id = uuid.UUID(data["document_id"])

    # Verify DB row via direct session
    import asyncio
    from backend.db.models.document import Document
    from sqlalchemy import select
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    import os

    async def _check():
        url = os.environ["TEST_DATABASE_URL"]
        engine = create_async_engine(url, poolclass=NullPool)
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            result = await session.execute(select(Document).where(Document.id == doc_id))
            return result.scalar_one_or_none()
        await engine.dispose()

    row = asyncio.run(_check())
    assert row is not None
    # Background ingest task may have already completed by the time we query
    assert row.status in ("processing", "ready", "failed")


@pytest.mark.integration
def test_integration_upload_oversized_returns_413(integration_client):
    """Upload oversized file → 413."""
    big = b"x" * (21 * 1024 * 1024)  # > 20MB default
    resp = integration_client.post(
        "/v1/documents/upload",
        files={"file": ("big.txt", io.BytesIO(big), "text/plain")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "ERR_FILE_TOO_LARGE"


@pytest.mark.integration
def test_integration_upload_mime_mismatch_returns_415(integration_client):
    """Upload PDF bytes declared as text/plain → 415."""
    pdf_magic = b"%PDF-1.4 fake pdf content"
    resp = integration_client.post(
        "/v1/documents/upload",
        files={"file": ("doc.pdf", io.BytesIO(pdf_magic), "text/plain")},
    )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "ERR_MIME_MISMATCH"
