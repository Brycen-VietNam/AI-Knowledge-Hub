# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S001
# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S003
# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S004
# Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S000
# Task: S001-T001 — FastAPI application factory
# Task: S003-T003 — Valkey connection pool at startup; RateLimiter singleton
# Task: S004-T002 — Register RAG exception handlers (A005 shape, no stack traces)
# Task: T005 — Register auth router (POST /v1/auth/token)
# Rule: R003 — all /v1/* endpoints require authentication (except /v1/auth/token — R003 exception)
# Rule: S004 — 60 req/min sliding window via Valkey (not per-request connection)
# Rule: A005 — error shape: {"error": {"code": ..., "message": ..., "request_id": ...}}
import uuid

import valkey.asyncio as valkey_asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.config import VALKEY_URL
from backend.api.middleware.rate_limiter import RateLimiter
from backend.api.routes import admin, auth, documents, query, upload, users
from backend.rag.embedder import EmbedderError
from backend.rag.llm import LLMError
from backend.rag.retriever import QueryTimeoutError
from backend.rag.parser.base import ParseError, SecurityError
from backend.rag.tokenizers.exceptions import LanguageDetectionError, UnsupportedLanguageError


def _error_body(request: Request, code: str, message: str) -> dict:
    """Build A005-compliant error body. request_id from state if set, else fresh UUID."""
    request_id = getattr(getattr(request, "state", None), "request_id", None) or str(uuid.uuid4())
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def create_app() -> FastAPI:
    app = FastAPI(title="Knowledge Hub API")

    # CORS: Allow frontend origins (dev: localhost:8080/8081, localhost:5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://localhost:8081", "http://localhost:5173", "http://127.0.0.1:8080", "http://127.0.0.1:8081", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # S003: create Valkey connection pool once at startup (not per-request)
    _valkey_client = valkey_asyncio.from_url(VALKEY_URL, decode_responses=False)
    _rate_limiter = RateLimiter(resource="query", limit=60, window=60)

    # Expose on app.state so query route can access them
    app.state.valkey_client = _valkey_client
    app.state.rate_limiter = _rate_limiter

    # S004-T002: RAG exception handlers — A005 shape, no stack traces
    @app.exception_handler(LanguageDetectionError)
    async def handle_lang_detect(request: Request, exc: LanguageDetectionError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(request, "LANG_DETECT_FAILED", str(exc) or "Language detection failed"),
        )

    @app.exception_handler(UnsupportedLanguageError)
    async def handle_unsupported_lang(request: Request, exc: UnsupportedLanguageError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(request, "UNSUPPORTED_LANGUAGE", str(exc) or "Unsupported language"),
        )

    @app.exception_handler(EmbedderError)
    async def handle_embedder(request: Request, exc: EmbedderError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=_error_body(request, "EMBEDDER_UNAVAILABLE", str(exc) or "Embedding service unavailable"),
        )

    @app.exception_handler(QueryTimeoutError)
    async def handle_query_timeout(request: Request, exc: QueryTimeoutError) -> JSONResponse:
        return JSONResponse(
            status_code=504,
            content=_error_body(request, "QUERY_TIMEOUT", str(exc) or "Query timed out"),
        )

    @app.exception_handler(LLMError)
    async def handle_llm_error(request: Request, exc: LLMError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=_error_body(request, "LLM_UNAVAILABLE", str(exc) or "LLM service unavailable"),
        )

    # S004: ParseError → 422; SecurityError → 413/415 (A005 shape)
    @app.exception_handler(ParseError)
    async def handle_parse_error(request: Request, exc: ParseError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(request, exc.code, str(exc)),
        )

    @app.exception_handler(SecurityError)
    async def handle_security_error(request: Request, exc: SecurityError) -> JSONResponse:
        status = 413 if exc.code == "ERR_FILE_TOO_LARGE" else 415
        return JSONResponse(
            status_code=status,
            content=_error_body(request, exc.code, str(exc)),
        )

    app.include_router(query.router)
    app.include_router(documents.router)
    app.include_router(upload.router)
    app.include_router(auth.router)   # T005: public login endpoint (R003 exception)
    app.include_router(users.router)  # S001/T006: self-service user endpoints
    app.include_router(admin.router)  # S000/T010: admin endpoints (require_admin guard)
    return app


app = create_app()
