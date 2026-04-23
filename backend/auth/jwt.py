# Spec: docs/security-audit/spec/security-audit.spec.md#S001
# Task: T001 — jwt.py: create_access_token, create_refresh_token, verify_refresh_token
# Decision: D-SA-01 — JWT_REFRESH_SECRET separate from AUTH_SECRET_KEY (independent rotation)
# Decision: D-SA-03 — token_version claim shortened to 'tv'
# Rule: S005 — all secrets from env; RuntimeError at startup if absent
import datetime
import os

import jwt as _pyjwt

_AUTH_SECRET_KEY: str | None = os.getenv("AUTH_SECRET_KEY")
if not _AUTH_SECRET_KEY:
    raise RuntimeError("Missing required env var: AUTH_SECRET_KEY")

_JWT_REFRESH_SECRET: str | None = os.getenv("JWT_REFRESH_SECRET")
if not _JWT_REFRESH_SECRET:
    raise RuntimeError("Missing required env var: JWT_REFRESH_SECRET")

_AUTH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))
_AUTH_REFRESH_TOKEN_EXPIRE_HOURS: int = int(os.getenv("AUTH_REFRESH_TOKEN_EXPIRE_HOURS", "8"))


def create_access_token(sub: str, user_id: str, token_version: int = 1) -> str:
    """Issue HS256 access JWT. token_version param accepted (S002 embeds 'tv' claim)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(minutes=_AUTH_TOKEN_EXPIRE_MINUTES)
    return _pyjwt.encode(
        {
            "sub": sub,
            "user_id": str(user_id),
            "tv": token_version,
            "exp": expire,
            "iat": now,
        },
        _AUTH_SECRET_KEY,
        algorithm="HS256",
    )


def create_refresh_token(sub: str, user_id: str) -> str:
    """Issue HS256 refresh JWT using JWT_REFRESH_SECRET (D-SA-01)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(hours=_AUTH_REFRESH_TOKEN_EXPIRE_HOURS)
    return _pyjwt.encode(
        {
            "sub": sub,
            "user_id": str(user_id),
            "exp": expire,
            "iat": now,
        },
        _JWT_REFRESH_SECRET,
        algorithm="HS256",
    )


def create_refresh_token_expires_in() -> int:
    """Return refresh token TTL in seconds (for response body)."""
    return _AUTH_REFRESH_TOKEN_EXPIRE_HOURS * 3600


def verify_refresh_token(token: str) -> dict:
    """Decode and validate refresh token. Raises ValueError on any failure."""
    try:
        return _pyjwt.decode(
            token,
            _JWT_REFRESH_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "sub", "user_id"]},
        )
    except _pyjwt.PyJWTError as exc:
        raise ValueError(f"Invalid refresh token: {exc}") from exc
