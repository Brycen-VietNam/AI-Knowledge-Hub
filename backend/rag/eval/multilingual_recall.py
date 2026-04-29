# Spec: docs/embed-model-migration/spec/embed-model-migration.spec.md#S005
# Task: S005-T003 — eval harness CLI (recall@10 + MRR, --model flag, pgvector <=> search)
# Decision: D09 — pass bar recall@10 ≥ 0.6 overall, ≥ 0.5 cross-lingual
"""
Multilingual recall@10 / MRR evaluation harness.

Usage:
    python -m backend.rag.eval.multilingual_recall --model zylonai/multilingual-e5-large

Requires: live Ollama + populated PostgreSQL (run S004 truncate + re-ingest first).
CI: integration tests skipped via pytest.mark.integration gate — see tests/rag/test_multilingual_recall.py.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.rag.embedder import OllamaEmbedder

FIXTURES_PATH = Path(__file__).parent / "multilingual_recall.fixtures.json"

PASS_BAR_OVERALL = 0.6
PASS_BAR_CROSS_LINGUAL = 0.5


def _load_fixtures() -> dict[str, Any]:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)


async def _pgvector_top10(
    session: AsyncSession,
    query_vec: list[float],
) -> list[str]:
    """Return top-10 doc_id strings via pgvector cosine <=> search (no RBAC — eval uses public docs)."""
    sql = text("""
        SELECT e.doc_id::text
        FROM embeddings e
        WHERE e.user_group_id IS NULL
        ORDER BY e.embedding <=> cast(:query_vec AS vector)
        LIMIT 10
    """).bindparams(query_vec=str(query_vec))
    rows = await session.execute(sql)
    return [r[0] for r in rows]


def _compute_metrics(
    hits: list[bool],
    ranks: list[int | None],
    queries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute recall@10 and MRR globally, per lang, per category."""
    total = len(hits)
    recall_global = sum(hits) / total if total else 0.0
    mrr_global = sum(1.0 / r for r in ranks if r is not None) / total if total else 0.0

    langs = sorted({q["query_lang"] for q in queries})
    categories = sorted({q["category"] for q in queries})

    per_lang: dict[str, dict[str, float]] = {}
    for lang in langs:
        idx = [i for i, q in enumerate(queries) if q["query_lang"] == lang]
        n = len(idx)
        per_lang[lang] = {
            "recall_at_10": sum(hits[i] for i in idx) / n if n else 0.0,
            "mrr": sum(1.0 / ranks[i] for i in idx if ranks[i] is not None) / n if n else 0.0,
            "count": n,
        }

    per_category: dict[str, dict[str, float]] = {}
    for cat in categories:
        idx = [i for i, q in enumerate(queries) if q["category"] == cat]
        n = len(idx)
        per_category[cat] = {
            "recall_at_10": sum(hits[i] for i in idx) / n if n else 0.0,
            "mrr": sum(1.0 / ranks[i] for i in idx if ranks[i] is not None) / n if n else 0.0,
            "count": n,
        }

    cross_idx = [i for i, q in enumerate(queries) if q["category"] == "cross-lingual"]
    n_cross = len(cross_idx)
    cross_recall = sum(hits[i] for i in cross_idx) / n_cross if n_cross else 0.0

    verdict_overall = "PASS" if recall_global >= PASS_BAR_OVERALL else "FAIL"
    verdict_cross = "PASS" if cross_recall >= PASS_BAR_CROSS_LINGUAL else "FAIL"

    return {
        "global": {
            "recall_at_10": recall_global,
            "mrr": mrr_global,
            "total": total,
            "verdict_overall": verdict_overall,
            "verdict_cross_lingual": verdict_cross,
        },
        "cross_lingual": {
            "recall_at_10": cross_recall,
            "count": n_cross,
        },
        "per_lang": per_lang,
        "per_category": per_category,
    }


async def run_eval(model: str | None = None) -> dict[str, Any]:
    """Run full eval: embed all queries (batched) → pgvector top-10 → recall@10 + MRR."""
    if model:
        os.environ["EMBEDDING_MODEL"] = model

    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url, pool_size=5, max_overflow=0)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    data = _load_fixtures()
    queries = data["queries"]

    embedder = OllamaEmbedder()

    # P002: batch embed all queries together (not serial per-query)
    query_texts = [q["query"] for q in queries]
    batch_size = 32
    query_vecs: list[list[float]] = []
    for i in range(0, len(query_texts), batch_size):
        batch = query_texts[i : i + batch_size]
        vecs = await asyncio.gather(*[embedder.embed_query(t) for t in batch])
        query_vecs.extend(vecs)

    hits: list[bool] = []
    ranks: list[int | None] = []

    async with AsyncSessionLocal() as session:
        for q, vec in zip(queries, query_vecs):
            top10_ids = await _pgvector_top10(session, vec)
            expected = set(q["expected_doc_ids"])
            hit = any(doc_id in expected for doc_id in top10_ids)
            hits.append(hit)
            rank: int | None = None
            for pos, doc_id in enumerate(top10_ids, start=1):
                if doc_id in expected:
                    rank = pos
                    break
            ranks.append(rank)

    await engine.dispose()
    return _compute_metrics(hits, ranks, queries)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multilingual recall@10 eval harness")
    parser.add_argument("--model", type=str, default=None, help="Override EMBEDDING_MODEL env var (AC6)")
    args = parser.parse_args()

    result = asyncio.run(run_eval(model=args.model))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
