# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S003-ext/T001 — MdParser (Markdown support)
# Decision: preserve raw Markdown text (headings, code fences, lists intact for chunker)
import re

from .base import ParsedDocument, ParserBase


class MdParser(ParserBase):
    def parse(self, data: bytes) -> ParsedDocument:
        # FIX-T007: use utf-8 with replacement characters — latin-1 causes CJK mojibake
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")

        # Collapse runs of 3+ newlines to a maximum of 2
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return ParsedDocument(
            text=text,
            lang=None,
            metadata={"source_format": "md"},
        )
