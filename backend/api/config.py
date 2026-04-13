# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S003
# Task: S003-T001 — VALKEY_URL env var config
# Rule: S005 — no hardcoded credentials; all via environment variables
import os

# Valkey connection URL — A3: new var, not present in prior config
# Default to localhost for local dev; override via VALKEY_URL in all other envs
VALKEY_URL: str = os.getenv("VALKEY_URL", "valkey://localhost:6379")

