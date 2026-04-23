# Spec: docs/change-password/spec/change-password.spec.md#S001
# Task: S001/T003 — reusable password-generation helper
import secrets
import string


def generate_password(length: int = 16) -> str:
    """Return a cryptographically random password of the given length.

    Uses secrets module (not random) per SECURITY.md. Character set: ASCII
    letters + digits + safe punctuation (no ambiguous chars or quotes).
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+?"
    return "".join(secrets.choice(alphabet) for _ in range(length))
