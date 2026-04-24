# conftest.py — tests/auth/
# Set OIDC stub env vars before any auth module is imported.
# oidc.py raises RuntimeError at import time when OIDC_ISSUER/AUDIENCE/JWKS_URI are absent.
# This conftest ensures the whole tests/auth/ directory can collect without a live IdP.
import os

_OIDC_STUBS = {
    "OIDC_ISSUER": "https://keycloak.test/realms/brysen",
    "OIDC_AUDIENCE": "knowledge-hub",
    "OIDC_JWKS_URI": "https://keycloak.test/realms/brysen/protocol/openid-connect/certs",
    "AUTH_SECRET_KEY": "test-auth-secret-key-for-tests",
    "JWT_REFRESH_SECRET": "test-refresh-secret-key-for-tests",
}
for _k, _v in _OIDC_STUBS.items():
    os.environ.setdefault(_k, _v)
