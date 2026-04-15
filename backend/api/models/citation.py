# Spec: docs/answer-citation/spec/answer-citation.spec.md#S002
# Task: S002-T001 — CitationObject Pydantic v2 model
# Decision: D-CIT-01 (additive), D-CIT-03 (no score filter), D-CIT-05 (API layer builds from RetrievedDocument)
# Rule: R002 — no PII (no user_id, email, chunk content, group_id)
from pydantic import BaseModel


class CitationObject(BaseModel):
    doc_id: str
    title: str
    source_url: str | None = None
    chunk_index: int
    score: float
    lang: str
