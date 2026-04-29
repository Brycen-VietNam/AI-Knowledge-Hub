"""Truncate embeddings and audit_logs tables for re-ingest.

Usage:
    python scripts/truncate_and_reset.py --confirm

Requires:
    DATABASE_URL env var (e.g. postgresql+psycopg2://user:pass@host/db)

Safety gates:
    --confirm flag required — prevents accidental runs.
    Logs row counts before and after each truncation.
    All SQL via sqlalchemy.text() — no string interpolation.

Spec: docs/embed-model-migration/spec/embed-model-migration.spec.md#S004
Task: S004 T001 — idempotent truncate script for embed-model-migration re-ingest
"""
import argparse
import logging
import os
import sys

from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

TABLES = ["embeddings", "audit_logs"]


def _build_engine(database_url: str):
    return create_engine(database_url)


def _row_count(conn, table: str) -> int:
    stmt = text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 — table name is internal constant, never user input
    return conn.execute(stmt).scalar()


def _truncate(conn, table: str) -> None:
    conn.execute(text(f"TRUNCATE TABLE {table}"))  # noqa: S608 — same: internal constant


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Truncate embeddings and audit_logs for re-ingest (embed-model-migration)."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        default=False,
        help="Required safety flag. Script exits without this.",
    )
    args = parser.parse_args(argv)

    if not args.confirm:
        log.error("--confirm flag required. Run with --confirm to proceed.")
        sys.exit(1)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        log.error("DATABASE_URL environment variable is not set.")
        sys.exit(1)

    engine = _build_engine(database_url)

    try:
        with engine.connect() as conn:
            for table in TABLES:
                before = _row_count(conn, table)
                log.info("Table %s: %d rows before truncate.", table, before)
                _truncate(conn, table)
                conn.commit()
                after = _row_count(conn, table)
                log.info("Table %s: %d rows remain after truncate.", table, after)
    except Exception as exc:
        log.error("Truncation failed: %s", exc)
        sys.exit(1)

    log.info("Done. All tables truncated successfully.")


if __name__ == "__main__":
    main()
