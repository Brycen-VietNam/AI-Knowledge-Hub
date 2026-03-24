# Spec: docs/specs/db-schema-embeddings.spec.md#S001, docs/specs/auth-api-key-oidc.spec.md#S001
# Task: T004 — AuditLog user_id TEXT→UUID FK (auth-api-key-oidc)
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    doc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    query_hash: Mapped[str] = mapped_column(nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
