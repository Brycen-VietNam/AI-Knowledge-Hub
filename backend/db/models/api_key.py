# Spec: docs/specs/auth-api-key-oidc.spec.md#S001
# Task: T003 — ApiKey ORM model
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash: Mapped[str] = mapped_column(unique=True, nullable=False)
    user_group_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
