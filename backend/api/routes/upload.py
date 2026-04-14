# Spec: docs/document-parser/spec/document-parser.spec.md#S004
# Task: S004/T001 — POST /v1/documents/upload (multipart/form-data)
# Rule: R003 — verify_token on every endpoint
# Rule: R004 — /v1/ prefix required
# Rule: R006 — audit_log before background_tasks dispatch
# Decision: D04 — api_key write gate (inherits D09 from document-ingestion)
# Decision: D05 — lang resolution: provided → parser-detected → langdetect (A003, never "en" hardcode)
# Decision: D10 — title defaults to Path(filename).stem
# Decision: D11 — PARSER_TIMEOUT_SECS env var; asyncio.wait_for; 504 on timeout
# Decision: D12 — SecurityGate size check first (OOM prevention)
import asyncio
import logging
import os
import unicodedata
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from langdetect import LangDetectException, detect

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes.documents import ingest_pipeline
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.db.models.document import Document
from backend.rag.parser.base import ParseError, SecurityError, UnsupportedFormatError
from backend.rag.parser.factory import ParserFactory
from backend.rag.parser.security_gate import SecurityGate

PARSER_TIMEOUT_SECS = float(os.getenv("PARSER_TIMEOUT_SECS", "30"))

router = APIRouter()


def _error(request: Request, code: str, message: str) -> dict:
    request_id = getattr(getattr(request, "state", None), "request_id", None) or str(uuid.uuid4())
    return {"error": {"code": code, "message": message, "request_id": request_id}}


async def _write_audit_log(user_id: uuid.UUID, doc_id: uuid.UUID) -> None:
    """Write audit_log row for document upload. Opens own session (R006).
    FIX-T003: query_hash uses sentinel "UPLOAD" — uploads have no query; column is NOT NULL.
    """
    from backend.db.models.audit_log import AuditLog
    from backend.db.session import async_session_factory

    async with async_session_factory() as session:
        async with session.begin():
            session.add(AuditLog(user_id=user_id, doc_id=doc_id, query_hash="UPLOAD"))


@router.post("/v1/documents/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile | None = None,
    title: str | None = Form(default=None, max_length=500),
    user_group_id: int | None = Form(default=None),
    lang: str | None = Form(default=None),
) -> JSONResponse:
    # Step 1: file required
    if file is None or not file.filename:
        return JSONResponse(
            status_code=422,
            content=_error(request, "ERR_NO_FILE", "No file provided"),
        )

    # D04: api_key write gate
    if user.auth_type != "api_key":
        return JSONResponse(
            status_code=403,
            content=_error(request, "FORBIDDEN", "Write access requires API-key authentication"),
        )

    declared_mime = file.content_type or "application/octet-stream"
    # FIX-T004: strip control characters and cap at 255 chars to prevent log injection
    filename = "".join(
        c for c in (file.filename or "") if unicodedata.category(c) != "Cc"
    )[:255]

    # Step 2: size-first pre-read check (D12)
    gate = SecurityGate()
    file_size = file.size or 0
    try:
        gate.validate(file_size, b"", declared_mime, filename)
    except SecurityError as exc:
        # FIX-T008 Option B: re-log at route layer with request_id for production traceability
        err = _error(request, exc.code, str(exc))
        logger.warning("SecurityGate rejected upload request_id=%s code=%s", err["error"]["request_id"], exc.code)
        status = 413 if exc.code == "ERR_FILE_TOO_LARGE" else 415
        return JSONResponse(status_code=status, content=err)

    # Step 3: chunked read with byte counter — aborts on limit exceeded (FIX-T006)
    limit = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    chunks: list[bytes] = []
    total_read = 0
    chunk_size = 65536  # 64KB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > limit:
            return JSONResponse(
                status_code=413,
                content=_error(request, "ERR_FILE_TOO_LARGE", f"File size exceeds limit of {limit} bytes"),
            )
        chunks.append(chunk)
    content_bytes = b"".join(chunks)

    try:
        gate.validate(len(content_bytes), content_bytes, declared_mime, filename)
    except SecurityError as exc:
        err = _error(request, exc.code, str(exc))
        logger.warning("SecurityGate rejected upload request_id=%s code=%s", err["error"]["request_id"], exc.code)
        status = 413 if exc.code == "ERR_FILE_TOO_LARGE" else 415
        return JSONResponse(status_code=status, content=err)

    # Step 4: get parser — 415 on unsupported format
    try:
        parser = ParserFactory.get_parser(declared_mime, filename)
    except UnsupportedFormatError as exc:
        return JSONResponse(
            status_code=415,
            content=_error(request, exc.code, str(exc)),
        )

    # Step 5: parse with timeout
    try:
        parsed = await asyncio.wait_for(
            asyncio.to_thread(parser.parse, content_bytes),
            timeout=PARSER_TIMEOUT_SECS,
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content=_error(request, "ERR_PARSE_TIMEOUT", "File parsing timed out"),
        )
    except ParseError as exc:
        return JSONResponse(
            status_code=422,
            content=_error(request, exc.code, str(exc)),
        )

    # Step 6–7: resolve title and lang (FIX-T001: A003 — never hardcode "en" fallback)
    # D05: provided → parser-detected → langdetect auto-detect → None (downstream handles)
    resolved_title = title or Path(filename).stem
    if lang:
        resolved_lang: str | None = lang
    elif parsed.lang:
        resolved_lang = parsed.lang
    else:
        try:
            resolved_lang = detect(parsed.text)
        except LangDetectException:
            resolved_lang = None  # store NULL; downstream chunker handles

    # Step 8: INSERT Document row
    doc = Document(
        title=resolved_title,
        lang=resolved_lang,
        user_group_id=user_group_id,
        status="processing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Step 9: audit log (R006) — before background dispatch
    await _write_audit_log(user.user_id, doc.id)

    # Step 10: dispatch ingestion pipeline in background
    background_tasks.add_task(ingest_pipeline, doc.id, parsed.text)

    # Step 11: 202 response
    return JSONResponse(
        status_code=202,
        content={"document_id": str(doc.id), "status": "processing"},
    )
