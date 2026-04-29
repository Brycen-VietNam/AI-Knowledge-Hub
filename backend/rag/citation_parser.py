"""
citation_parser.py — Pure citation marker extraction.

Spec: docs/citation-quality/spec/citation-quality.spec.md#S001
Task: S001-T001 — _parse_citations() pure module
Decisions:
  D-CQ-03: OOB markers silently ignored
  D-CQ-04: Parser output is 0-based; input markers are 1-based
"""

import re


def _parse_citations(answer: str, num_docs: int) -> set[int]:
    """Extract 0-based citation indices from an LLM answer string.

    Scans `answer` for inline markers of the form [N] (1-based, N ≥ 1).
    Returns the set of 0-based indices that are within bounds [0, num_docs).
    Out-of-bounds and duplicate markers are silently ignored (D-CQ-03).

    Args:
        answer:   LLM-generated answer text, possibly containing [N] markers.
        num_docs: Number of content documents (upper bound for valid indices).

    Returns:
        Set of 0-based integers, each < num_docs.  Empty set when no valid
        markers are present or when answer/num_docs is empty/zero.
    """
    if not answer or num_docs <= 0:
        return set()

    # Support multiple marker formats that LLMs emit in practice:
    #   [N]  [N†...]  【N†...】  (N)
    raw: list[str] = re.findall(
        r"\[\s*(\d+)[^\]]*\]"   # [N] or [N†L1-L4]
        r"|【\s*(\d+)[^】]*】"   # 【N†...】
        r"|\(\s*(\d+)\s*\)",    # (N)
        answer,
    )
    cited: set[int] = set()
    for groups in raw:
        token = next(g for g in groups if g)
        zero_based = int(token) - 1
        if 0 <= zero_based < num_docs:
            cited.add(zero_based)
    return cited
