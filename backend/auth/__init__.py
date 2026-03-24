# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Task: T003 — public interface for backend.auth package
# Rule: A001 — agent scope isolation; internal functions intentionally unexported (AC5)
# Internal functions (verify_api_key, verify_oidc_token, auth_error, _errors) are NOT
# re-exported here — api-agent must import only through this interface.
from .dependencies import verify_token
from .types import AuthenticatedUser

__all__ = ["verify_token", "AuthenticatedUser"]
