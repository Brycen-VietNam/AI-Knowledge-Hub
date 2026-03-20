# Spec: docs/specs/db-schema-embeddings.spec.md#S001
# Task: T002 — AuditLog ORM model (C008)
# Note: user_id is TEXT placeholder — FK added by auth-agent (auth-api-key-oidc spec)
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(nullable=False)  # TEXT placeholder; FK added by auth-agent
    doc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    query_hash: Mapped[str] = mapped_column(nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
