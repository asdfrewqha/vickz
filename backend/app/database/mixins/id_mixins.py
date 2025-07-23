from uuid import UUID as uuid
from uuid_v7.base import uuid7
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column


class IDMixin:
    id: Mapped[uuid] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
