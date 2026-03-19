# Spec: docs/specs/db-schema-embeddings.spec.md#S003
# Task: T002 — Add content_fts tsvector column (migration 003 required)
# Decision: D02 — CJK tokenization in app layer, not pg trigger
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    lang: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 639-1
    user_group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    # updated_at must be set by application layer on UPDATE (no DB trigger)
    content_fts: Mapped[str | None] = mapped_column(Text().with_variant(TSVECTOR, "postgresql"), nullable=True)  # nullable: rag-agent populates post-ingestion (D02)
