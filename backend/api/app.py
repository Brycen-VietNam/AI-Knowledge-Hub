# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S001
# Task: S001-T001 — FastAPI application factory
# Rule: R003 — all /v1/* endpoints require authentication
from fastapi import FastAPI

from backend.api.routes import query, documents


def create_app() -> FastAPI:
    app = FastAPI(title="Knowledge Hub API")
    app.include_router(query.router)
    app.include_router(documents.router)
    return app


app = create_app()
