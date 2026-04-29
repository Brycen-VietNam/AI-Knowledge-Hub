"""
Seed eval fixture documents into documents + embeddings tables.
Reads ingest_docs from multilingual_recall.fixtures.json, upserts each doc into
documents table, embeds text via OllamaEmbedder, and upserts into embeddings.
user_group_id=NULL (public docs — required by eval harness pgvector query).

Usage:
    docker exec knowledge-hub-app python scripts/seed_eval_fixtures.py
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.rag.embedder import OllamaEmbedder

FIXTURES_PATH = Path(__file__).parent.parent / "backend/rag/eval/multilingual_recall.fixtures.json"


async def seed() -> None:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        data = json.load(f)

    docs = data["ingest_docs"]
    print(f"Seeding {len(docs)} documents...")

    embedder = OllamaEmbedder()

    # P002: batch embed all passages together
    texts = [d["text"] for d in docs]
    vecs = await asyncio.gather(*[embedder.embed_passage(t) for t in texts])

    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url, pool_size=5, max_overflow=0)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        for doc, vec in zip(docs, vecs):
            doc_uuid = uuid.UUID(doc["doc_id"])
            lang = doc["lang"][:2]

            # 1. Upsert into documents (FK parent)
            await session.execute(
                text("""
                    INSERT INTO documents (id, title, lang, user_group_id, status)
                    VALUES (:id, :title, :lang, NULL, 'ready')
                    ON CONFLICT (id) DO UPDATE
                        SET title = EXCLUDED.title,
                            lang  = EXCLUDED.lang,
                            status = 'ready'
                """).bindparams(
                    id=doc_uuid,
                    title=doc["title"],
                    lang=lang,
                )
            )

            # 2. Replace embeddings for this doc (no unique constraint on doc_id+chunk_index)
            await session.execute(
                text("DELETE FROM embeddings WHERE doc_id = :doc_id").bindparams(doc_id=doc_uuid)
            )
            await session.execute(
                text("""
                    INSERT INTO embeddings (doc_id, chunk_index, lang, user_group_id, embedding, text)
                    VALUES (:doc_id, 0, :lang, NULL, cast(:embedding AS vector), :text)
                """).bindparams(
                    doc_id=doc_uuid,
                    lang=lang,
                    embedding=str(vec),
                    text=doc["text"],
                )
            )
            print(f"  ✓ {doc['doc_id']} [{lang}] {doc['title'][:55]}")

        await session.commit()

    await engine.dispose()
    print(f"\nDone — {len(docs)} documents seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
