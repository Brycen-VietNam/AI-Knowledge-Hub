# Spec: docs/specs/auth-api-key-oidc.spec.md#S004
# Task: T001 — AuthenticatedUser canonical definition (moved from api_key.py)
# Decision: D12 — types.py avoids circular import (api_key + oidc both import here;
#            dependencies.py imports from both without cycle)
# Rule: AC1 — frozen=True prevents accidental mutation of auth context in handlers
import uuid
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AuthenticatedUser:
    """Immutable auth context injected into every authenticated request handler."""
    user_id: uuid.UUID
    user_group_ids: list[int]
    auth_type: Literal["api_key", "oidc"]
    # Spec: docs/admin-spa/spec/admin-spa.spec.md#S000/AC2
    # Task: S000/T003 — computed by verify_token from user_group_memberships JOIN
    is_admin: bool = False
