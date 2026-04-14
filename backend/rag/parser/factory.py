# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S001/T003 — ParserFactory MIME-type dispatch
# Decision: D01 — primary dispatch by MIME; extension fallback for octet-stream only
import importlib
import pathlib

from .base import ParserBase, UnsupportedFormatError

_MIME_MAP: dict[str, str] = {
    "application/pdf": "backend.rag.parser.pdf_parser.PdfParser",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        "backend.rag.parser.docx_parser.DocxParser"
    ),
    "text/html": "backend.rag.parser.html_parser.HtmlParser",
    "text/plain": "backend.rag.parser.txt_parser.TxtParser",
    "text/markdown": "backend.rag.parser.md_parser.MdParser",
}

_EXT_MAP: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".html": "text/html",
    ".htm": "text/html",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


class ParserFactory:
    @staticmethod
    def get_parser(mime_type: str, filename: str) -> ParserBase:
        effective_mime = mime_type
        if mime_type == "application/octet-stream":
            ext = pathlib.Path(filename).suffix.lower()
            effective_mime = _EXT_MAP.get(ext, mime_type)

        if effective_mime not in _MIME_MAP:
            raise UnsupportedFormatError(effective_mime)

        # Lazy import to avoid circular deps with __init__.py
        dotted = _MIME_MAP[effective_mime]
        module_path, class_name = dotted.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)()
