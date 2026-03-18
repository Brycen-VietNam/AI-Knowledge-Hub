# Spec: docs/specs/db-schema-embeddings.spec.md#S001
# Task: T002 — Embedding ORM model (no Vector column yet — added in S002/T002)
# Decision: D01 — embedding vector(1024) added after pgvector extension (migration 002)
# Decision: D02 — user_group_id denormalized for RBAC WHERE clause (R001, C002)
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    lang: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 639-1
    user_group_id: Mapped[int] = mapped_column(nullable=False)  # denormalized, no FK (R001)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    # embedding Vector(1024) column added in S002/T002 after pgvector extension
