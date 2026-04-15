# Spec: docs/answer-citation/spec/answer-citation.spec.md#S002
# Spec: docs/citation-quality/spec/citation-quality.spec.md#S002
# Task: S002-T001 — CitationObject Pydantic v2 model
# Task: citation-quality/S002-T001 — add cited: bool = False (D-CQ-01 additive, zero breakage)
# Decision: D-CIT-01 (additive), D-CIT-03 (no score filter), D-CIT-05 (API layer builds from RetrievedDocument)
# Decision: D-CQ-01 — cited default False = backward-compatible (no consumer breakage)
# Rule: R002 — no PII (no user_id, email, chunk content, group_id)
from pydantic import BaseModel


class CitationObject(BaseModel):
    doc_id: str
    title: str
    source_url: str | None = None
    chunk_index: int
    score: float
    lang: str
    cited: bool = False  # D-CQ-01: True only when LLM emitted [N] marker for this doc
