"""
Task: S003-ext/T001 — MdParser tests (TDD)
Spec: docs/document-parser/spec/document-parser.spec.md
"""
from backend.rag.parser.md_parser import MdParser


def test_utf8_markdown_decoded_correctly():
    """UTF-8 Markdown bytes → text decoded; source_format == 'md'; lang is None."""
    data = b"# Hello\n\nThis is a **markdown** file."
    parser = MdParser()
    doc = parser.parse(data)

    assert "# Hello" in doc.text
    assert "**markdown**" in doc.text
    assert doc.lang is None
    assert doc.metadata["source_format"] == "md"


def test_cjk_content_preserved():
    """UTF-8 CJK characters inside Markdown → preserved in output."""
    md_text = "## セクション\n\nこれはテストです。"
    data = md_text.encode("utf-8")
    parser = MdParser()
    doc = parser.parse(data)

    assert "## セクション" in doc.text
    assert "これはテストです。" in doc.text
    assert doc.lang is None


def test_headings_preserved_verbatim():
    """Markdown headings (# / ##) are NOT transformed — passed through as-is."""
    data = b"# Title\n\n## Section\n\n### Sub\n\nContent here."
    parser = MdParser()
    doc = parser.parse(data)

    assert "# Title" in doc.text
    assert "## Section" in doc.text
    assert "### Sub" in doc.text


def test_code_fences_preserved():
    """Fenced code blocks are preserved verbatim."""
    md_text = "Some text\n\n```python\nprint('hello')\n```\n\nMore text."
    data = md_text.encode("utf-8")
    parser = MdParser()
    doc = parser.parse(data)

    assert "```python" in doc.text
    assert "print('hello')" in doc.text
    assert "```" in doc.text


def test_excessive_newlines_collapsed():
    """More than 2 consecutive newlines → collapsed to max 2."""
    data = "First section\n\n\n\n\nSecond section".encode("utf-8")
    parser = MdParser()
    doc = parser.parse(data)

    assert "\n\n\n" not in doc.text
    assert "First section" in doc.text
    assert "Second section" in doc.text


def test_md_parser_japanese_utf8_no_mojibake():
    """FIX-T007: non-UTF-8 bytes fall back to utf-8 errors=replace — no latin-1 mojibake."""
    # Construct bytes that are NOT valid UTF-8 (lone continuation byte)
    # This simulates a corrupted file; latin-1 would produce garbage CJK.
    bad_bytes = b"## \xe3\x81\x82"  # valid UTF-8 for あ
    parser = MdParser()
    doc = parser.parse(bad_bytes)
    assert "## あ" in doc.text  # correct UTF-8 decoding, no mojibake

    # Truly invalid UTF-8: replacement char expected, NOT latin-1 garbage
    invalid_utf8 = b"title: \x80\x81\x82"
    doc2 = parser.parse(invalid_utf8)
    # latin-1 would give "title: €" — utf-8 errors=replace gives "title: \ufffd\ufffd\ufffd"
    assert "\ufffd" in doc2.text
    assert "€" not in doc2.text
