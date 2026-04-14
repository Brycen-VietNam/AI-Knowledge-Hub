"""
Task: S002/T001 — PdfParser tests (TDD)
Spec: docs/document-parser/spec/document-parser.spec.md
"""
import io
import time

import pytest
import pdfplumber
from reportlab.pdfgen import canvas  # type: ignore[import]
from reportlab.lib.pagesizes import letter  # type: ignore[import]

from backend.rag.parser.pdf_parser import PdfParser
from backend.rag.parser.base import ParseError


# ---------------------------------------------------------------------------
# Helpers — minimal PDF byte builders
# ---------------------------------------------------------------------------

def _make_pdf_bytes(*page_texts: str) -> bytes:
    """Build a minimal multi-page PDF with text layers via reportlab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for text in page_texts:
        c.drawString(72, 700, text)
        c.showPage()
    c.save()
    return buf.getvalue()


def _make_image_only_pdf() -> bytes:
    """Build a PDF with one blank page (no text layer)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_multipage_pdf_text_and_metadata():
    """3-page PDF → text joined with double-newline, page_count=3."""
    data = _make_pdf_bytes("Page one text", "Page two text", "Page three text")
    parser = PdfParser()
    doc = parser.parse(data)

    assert "Page one text" in doc.text
    assert "Page two text" in doc.text
    assert "Page three text" in doc.text
    assert doc.metadata["page_count"] == 3
    assert len(doc.metadata["pages"]) == 3
    assert doc.metadata["source_format"] == "pdf"
    assert doc.lang is None


def test_single_page_pdf():
    """Single-page PDF → text extracted, page_count=1."""
    data = _make_pdf_bytes("Hello world")
    parser = PdfParser()
    doc = parser.parse(data)

    assert "Hello world" in doc.text
    assert doc.metadata["page_count"] == 1
    assert doc.lang is None


def test_image_only_pdf_raises_err_pdf_no_text():
    """PDF with no text layer → ParseError(ERR_PDF_NO_TEXT)."""
    data = _make_image_only_pdf()
    parser = PdfParser()

    with pytest.raises(ParseError) as exc_info:
        parser.parse(data)
    assert exc_info.value.code == "ERR_PDF_NO_TEXT"


def test_corrupt_pdf_raises_err_parse_failed():
    """Truncated/corrupt bytes → ParseError(ERR_PARSE_FAILED)."""
    parser = PdfParser()

    with pytest.raises(ParseError) as exc_info:
        parser.parse(b"%PDF-1.4 CORRUPT GARBAGE BYTES ####")
    assert exc_info.value.code == "ERR_PARSE_FAILED"


def test_pages_metadata_shape():
    """Each page entry has page_number (int) and text (str)."""
    data = _make_pdf_bytes("Alpha", "Beta")
    parser = PdfParser()
    doc = parser.parse(data)

    for i, pg in enumerate(doc.metadata["pages"], start=1):
        assert pg["page_number"] == i
        assert isinstance(pg["text"], str)


@pytest.mark.slow
def test_perf_large_pdf():
    """50-page PDF should parse in under 3 seconds."""
    pages = [f"This is page {i} of the performance test document." for i in range(1, 51)]
    data = _make_pdf_bytes(*pages)
    parser = PdfParser()

    start = time.monotonic()
    doc = parser.parse(data)
    elapsed = time.monotonic() - start

    assert doc.metadata["page_count"] == 50
    assert elapsed < 3.0, f"Parsing took {elapsed:.2f}s (limit: 3s)"
