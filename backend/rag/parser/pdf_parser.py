# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S002/T001 — PdfParser
# Decision: D01 (pdfplumber), D06 (image-only → ERR_PDF_NO_TEXT)
import io

import pdfplumber

from .base import ParseError, ParsedDocument, ParserBase


class PdfParser(ParserBase):
    def parse(self, data: bytes) -> ParsedDocument:
        try:
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                pages = [
                    {"page_number": i + 1, "text": (p.extract_text() or "")}
                    for i, p in enumerate(pdf.pages)
                ]
        except Exception as e:
            raise ParseError("ERR_PARSE_FAILED", str(e)) from e

        if not any(pg["text"].strip() for pg in pages):
            raise ParseError("ERR_PDF_NO_TEXT", "No text layer found in PDF")

        text = "\n\n".join(pg["text"] for pg in pages if pg["text"].strip())
        return ParsedDocument(
            text=text,
            lang=None,
            metadata={
                "page_count": len(pages),
                "pages": pages,
                "source_format": "pdf",
            },
        )
