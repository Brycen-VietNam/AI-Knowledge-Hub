# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S003/T002 — TxtParser
# Decision: UTF-8 first, latin-1 fallback (A003 — chunker handles lang detection)
import re

from .base import ParsedDocument, ParserBase


class TxtParser(ParserBase):
    def parse(self, data: bytes) -> ParsedDocument:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")

        # Collapse runs of 3+ newlines to a maximum of 2
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return ParsedDocument(
            text=text,
            lang=None,
            metadata={"source_format": "txt"},
        )
