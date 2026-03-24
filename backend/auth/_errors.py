# Spec: docs/specs/auth-api-key-oidc.spec.md#S002
# Task: T001 — auth package scaffold + _errors.py
# Rule: A005 — error response shape {"error": {"code", "message", "request_id"}}
# Note: fastapi imported lazily — not yet in requirements.txt (added in S003)
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import HTTPException, Request


def auth_error(request: "Request", code: str, message: str, status: int) -> "HTTPException":
    """Return A005-compliant HTTPException. request_id from middleware state or fresh UUID."""
    from fastapi import HTTPException  # lazy — fastapi added to requirements in S003
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    return HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": message, "request_id": request_id}},
    )
