# Spec: docs/document-parser/spec/document-parser.spec.md
# Task: S001/T001 — parser base types
# Constraints: R002/C002 — no PII in ParsedDocument.metadata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    text: str
    lang: str | None
    # Allowed fields: doc_id, created_at only — no email, name, or content snippets (R002)
    metadata: dict = field(default_factory=dict)


class ParserBase(ABC):
    @abstractmethod
    def parse(self, data: bytes) -> ParsedDocument: ...


class ParseError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class UnsupportedFormatError(ParseError):
    def __init__(self, mime_type: str) -> None:
        super().__init__(
            "ERR_UNSUPPORTED_FORMAT",
            f"Unsupported MIME type: {mime_type}",
        )
        self.mime_type = mime_type


class SecurityError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
