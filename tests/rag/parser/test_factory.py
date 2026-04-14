"""
Task: S001/T004 — ParserFactory dispatch tests (6 cases)
Spec: docs/document-parser/spec/document-parser.spec.md
"""
import pytest

from backend.rag.parser import (
    ParserFactory,
    UnsupportedFormatError,
)
from backend.rag.parser.docx_parser import DocxParser
from backend.rag.parser.html_parser import HtmlParser
from backend.rag.parser.pdf_parser import PdfParser
from backend.rag.parser.txt_parser import TxtParser

DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def test_pdf_mime_returns_pdf_parser():
    parser = ParserFactory.get_parser("application/pdf", "doc.pdf")
    assert isinstance(parser, PdfParser)


def test_docx_mime_returns_docx_parser():
    parser = ParserFactory.get_parser(DOCX_MIME, "doc.docx")
    assert isinstance(parser, DocxParser)


def test_html_mime_returns_html_parser():
    parser = ParserFactory.get_parser("text/html", "page.html")
    assert isinstance(parser, HtmlParser)


def test_txt_mime_returns_txt_parser():
    parser = ParserFactory.get_parser("text/plain", "readme.txt")
    assert isinstance(parser, TxtParser)


def test_unknown_mime_raises_unsupported_format_error():
    with pytest.raises(UnsupportedFormatError) as exc_info:
        ParserFactory.get_parser("application/x-unknown", "file.bin")
    assert "application/x-unknown" in str(exc_info.value)


def test_octet_stream_with_pdf_extension_returns_pdf_parser():
    parser = ParserFactory.get_parser("application/octet-stream", "report.pdf")
    assert isinstance(parser, PdfParser)
