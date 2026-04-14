"""
Task: S003/T001 — HtmlParser tests (TDD)
Spec: docs/document-parser/spec/document-parser.spec.md
"""
import pytest

from backend.rag.parser.html_parser import HtmlParser


def test_strips_html_tags():
    """Valid HTML → output contains no raw HTML tags."""
    html = b"<html><body><p>Hello world</p></body></html>"
    parser = HtmlParser()
    doc = parser.parse(html)

    assert "<p>" not in doc.text
    assert "<body>" not in doc.text
    assert "Hello world" in doc.text
    assert doc.lang is None
    assert doc.metadata["source_format"] == "html"


def test_strips_script_content():
    """<script> tag and its content are removed from output."""
    html = b"<html><body><script>alert(1)</script><p>Visible</p></body></html>"
    parser = HtmlParser()
    doc = parser.parse(html)

    assert "alert(1)" not in doc.text
    assert "Visible" in doc.text


def test_strips_style_content():
    """<style> tag and its content are removed from output."""
    html = b"<html><head><style>body{color:red}</style></head><body><p>Text</p></body></html>"
    parser = HtmlParser()
    doc = parser.parse(html)

    assert "color:red" not in doc.text
    assert "body{" not in doc.text
    assert "Text" in doc.text


def test_h1_produces_markdown_prefix():
    """<h1> heading → output contains '## Title'."""
    html = b"<html><body><h1>Title</h1><p>Body text</p></body></html>"
    parser = HtmlParser()
    doc = parser.parse(html)

    assert "## Title" in doc.text
    assert "Body text" in doc.text


def test_h3_produces_markdown_prefix():
    """<h3> heading → output contains '## Sub'."""
    html = b"<html><body><h3>Sub</h3><p>Content</p></body></html>"
    parser = HtmlParser()
    doc = parser.parse(html)

    assert "## Sub" in doc.text


def test_mixed_headings_script_style():
    """Complex document: headings kept, script/style stripped."""
    html = (
        b"<html><head><style>.x{}</style></head><body>"
        b"<h2>Chapter</h2><script>console.log('x')</script>"
        b"<p>Paragraph content</p><h4>Section</h4>"
        b"</body></html>"
    )
    parser = HtmlParser()
    doc = parser.parse(html)

    assert "## Chapter" in doc.text
    assert "## Section" in doc.text
    assert "console.log" not in doc.text
    assert ".x{}" not in doc.text
    assert "Paragraph content" in doc.text
    assert doc.lang is None
