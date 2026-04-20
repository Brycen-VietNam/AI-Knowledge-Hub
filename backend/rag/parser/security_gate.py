# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S003/T003 — SecurityGate
# Decision: D12 — size check BEFORE magic.from_buffer() to prevent OOM on large uploads
# Security: S003 (SECURITY.md) — MIME + magic-byte validation; S005 — env-configurable limit
import logging
import os

import magic  # type: ignore[import]

from .base import SecurityError

logger = logging.getLogger(__name__)

# MIME types that our parsers support — used to allow octet-stream declared uploads
_SUPPORTED_MIMES: frozenset[str] = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
    "text/plain",
    "text/markdown",
})


class SecurityGate:
    # Compatible MIME pairs — either direction is allowed
    _COMPATIBLE_PAIRS: frozenset[frozenset] = frozenset(
        [
            frozenset({"text/plain", "text/html"}),
            frozenset({"text/plain", "text/markdown"}),
        ]
    )

    def validate(
        self,
        file_size: int,
        file_bytes: bytes,
        declared_mime: str,
        filename: str,
    ) -> None:
        """Validate upload size and MIME type integrity.

        Step 1 — size check (D12: before reading bytes, prevents OOM).
        Step 2 — magic-byte check against declared MIME.
        """
        limit = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))

        if file_size > limit:
            logger.warning(
                "Rejected %s: file too large (%d bytes, limit %d)",
                filename,
                file_size,
                limit,
            )
            raise SecurityError(
                "ERR_FILE_TOO_LARGE",
                f"File size {file_size} exceeds limit of {limit} bytes",
            )

        # Skip magic-byte check when no bytes provided (size-only pre-read pass)
        if not file_bytes:
            return

        actual_mime = magic.from_buffer(file_bytes[:2048], mime=True)

        # application/octet-stream is a generic browser/tool fallback — accept if actual MIME
        # is one of the supported formats (ParserFactory handles extension-based dispatch).
        if declared_mime == "application/octet-stream" and actual_mime in _SUPPORTED_MIMES:
            return

        if not self._compatible(declared_mime, actual_mime):
            logger.warning(
                "Rejected %s: MIME mismatch declared=%s actual=%s",
                filename,
                declared_mime,
                actual_mime,
            )
            raise SecurityError(
                "ERR_MIME_MISMATCH",
                f"Declared MIME '{declared_mime}' does not match detected '{actual_mime}'",
            )

    @staticmethod
    def _compatible(declared: str, actual: str) -> bool:
        if declared == actual:
            return True
        return frozenset({declared, actual}) in SecurityGate._COMPATIBLE_PAIRS
