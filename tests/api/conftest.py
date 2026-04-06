# Stub OIDC env vars so backend.auth.oidc can be imported in unit tests
# without a real OIDC provider. Values are intentionally invalid — tests
# override verify_token via dependency injection and never call verify_oidc_token.
import os

os.environ.setdefault("OIDC_ISSUER", "https://test.example.com")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("OIDC_JWKS_URI", "https://test.example.com/.well-known/jwks.json")
