# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S003/T001 — HtmlParser
# Decision: D01 (beautifulsoup4, html.parser backend — no lxml dep)
import re

from bs4 import BeautifulSoup  # type: ignore[import]

from .base import ParsedDocument, ParserBase


class HtmlParser(ParserBase):
    def parse(self, data: bytes) -> ParsedDocument:
        html = data.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style tags with their contents entirely
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Convert h1–h6 to markdown-style prefix before stripping remaining tags
        for hdr in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            hdr.replace_with("## " + hdr.get_text() + "\n")

        text = soup.get_text(separator="\n")
        # Collapse 3+ consecutive newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return ParsedDocument(
            text=text,
            lang=None,
            metadata={"source_format": "html"},
        )
