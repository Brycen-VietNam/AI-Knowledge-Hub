# Spec: docs/change-password/spec/change-password.spec.md#S001
# Task: S001/T003 — test generate_password helper
import string

from backend.auth.utils import generate_password


class TestGeneratePassword:
    def test_default_length(self):
        pw = generate_password()
        assert len(pw) == 16

    def test_custom_length(self):
        pw = generate_password(length=24)
        assert len(pw) == 24

    def test_character_set(self):
        alphabet = set(string.ascii_letters + string.digits + "!@#$%^&*-_=+?")
        pw = generate_password(length=32)
        assert all(c in alphabet for c in pw)

    def test_randomness(self):
        # Probability of collision in 1000 calls is negligible for length=16
        passwords = {generate_password() for _ in range(100)}
        assert len(passwords) > 90
