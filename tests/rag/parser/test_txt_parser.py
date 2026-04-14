"""
Task: S003/T002 — TxtParser tests (TDD)
Spec: docs/document-parser/spec/document-parser.spec.md
"""
import pytest

from backend.rag.parser.txt_parser import TxtParser


def test_utf8_ascii_decoded_correctly():
    """ASCII UTF-8 bytes → text decoded correctly."""
    data = b"Hello, world! This is a plain text file."
    parser = TxtParser()
    doc = parser.parse(data)

    assert doc.text == "Hello, world! This is a plain text file."
    assert doc.lang is None
    assert doc.metadata["source_format"] == "txt"


def test_utf8_cjk_preserved():
    """UTF-8 CJK characters → decoded and preserved in output."""
    # Japanese: "これはテストです" (This is a test)
    cjk_text = "これはテストです。"
    data = cjk_text.encode("utf-8")
    parser = TxtParser()
    doc = parser.parse(data)

    assert cjk_text in doc.text
    assert doc.lang is None


def test_latin1_fallback():
    """Non-UTF-8 latin-1 bytes → decoded via fallback without error."""
    # é (0xe9) is invalid in UTF-8 as a standalone byte
    latin1_text = "Caf\xe9 au lait"
    data = latin1_text.encode("latin-1")
    parser = TxtParser()
    doc = parser.parse(data)

    assert "Caf" in doc.text
    assert doc.lang is None


def test_excessive_newlines_collapsed():
    """More than 2 consecutive newlines → collapsed to max 2."""
    data = "First paragraph\n\n\n\n\nSecond paragraph".encode("utf-8")
    parser = TxtParser()
    doc = parser.parse(data)

    assert "\n\n\n" not in doc.text
    assert "First paragraph" in doc.text
    assert "Second paragraph" in doc.text


def test_whitespace_normalized():
    """Text with excessive blank lines throughout is normalized."""
    lines = ["Line one", "", "", "", "Line two", "", "", "Line three"]
    data = "\n".join(lines).encode("utf-8")
    parser = TxtParser()
    doc = parser.parse(data)

    # Should not have 3+ consecutive newlines
    assert "\n\n\n" not in doc.text
    assert "Line one" in doc.text
    assert "Line two" in doc.text
    assert "Line three" in doc.text
