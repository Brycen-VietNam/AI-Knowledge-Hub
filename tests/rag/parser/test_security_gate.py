"""
Task: S003/T003 — SecurityGate tests (TDD)
Spec: docs/document-parser/spec/document-parser.spec.md
Decision: D12 — size check fires BEFORE magic.from_buffer() call
"""
import io
import os

import pytest

from backend.rag.parser.security_gate import SecurityGate
from backend.rag.parser.base import SecurityError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_pdf_bytes() -> bytes:
    """Return minimal valid PDF bytes that python-magic recognizes as PDF."""
    # Minimal PDF header + body that passes magic detection
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"xref\n0 2\n0000000000 65535 f \n"
        b"trailer\n<< /Size 2 /Root 1 0 R >>\nstartxref\n9\n%%EOF"
    )


def _plain_text_bytes() -> bytes:
    return b"This is plain text content for testing purposes."


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_pdf_passes():
    """Valid PDF bytes + declared application/pdf → no exception raised."""
    data = _minimal_pdf_bytes()
    gate = SecurityGate()
    # Should not raise
    gate.validate(
        file_size=len(data),
        file_bytes=data,
        declared_mime="application/pdf",
        filename="test.pdf",
    )


def test_size_check_fires_before_bytes_read():
    """file_size > MAX with tiny file_bytes → ERR_FILE_TOO_LARGE (size arg used, not len(bytes))."""
    gate = SecurityGate()
    huge_size = 21 * 1024 * 1024  # 21 MB — over default 20 MB limit
    tiny_bytes = b"tiny"  # length is only 4 — proves size param is what's checked

    with pytest.raises(SecurityError) as exc_info:
        gate.validate(
            file_size=huge_size,
            file_bytes=tiny_bytes,
            declared_mime="application/pdf",
            filename="large.pdf",
        )
    assert exc_info.value.code == "ERR_FILE_TOO_LARGE"


def test_mime_mismatch_pdf_declared_as_text():
    """PDF bytes declared as text/plain → ERR_MIME_MISMATCH."""
    data = _minimal_pdf_bytes()
    gate = SecurityGate()

    with pytest.raises(SecurityError) as exc_info:
        gate.validate(
            file_size=len(data),
            file_bytes=data,
            declared_mime="text/plain",
            filename="sneaky.txt",
        )
    assert exc_info.value.code == "ERR_MIME_MISMATCH"


def test_text_plain_and_text_html_are_compatible():
    """text/plain bytes declared as text/html → allowed (_compatible logic)."""
    data = _plain_text_bytes()
    gate = SecurityGate()
    # Should not raise — text/plain ↔ text/html are in compatible pairs
    gate.validate(
        file_size=len(data),
        file_bytes=data,
        declared_mime="text/html",
        filename="page.html",
    )


def test_env_override_max_upload_bytes(monkeypatch):
    """MAX_UPLOAD_BYTES env var override respected — 2KB file over 1KB limit rejected."""
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "1024")
    gate = SecurityGate()
    data = b"x" * 2048  # 2 KB

    with pytest.raises(SecurityError) as exc_info:
        gate.validate(
            file_size=2048,
            file_bytes=data,
            declared_mime="text/plain",
            filename="big.txt",
        )
    assert exc_info.value.code == "ERR_FILE_TOO_LARGE"
