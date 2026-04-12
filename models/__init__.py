import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    declared_attr,
    mapped_column,
)
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


class UuidTypeDecorator(TypeDecorator):
    """UUID を String(36) として MySQL に保存する TypeDecorator。"""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Optional[UUID], dialect) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return value  # type: ignore[unreachable]

    def process_result_value(self, value: Optional[str], dialect) -> Optional[UUID]:
        if value is None:
            return None
        if isinstance(value, str):
            return UUID(value)
        return value  # type: ignore[unreachable]

    @property
    def python_type(self):
        return UUID


class BaseModel(Base):
    """共通のベースモデル"""

    __abstract__ = True

    @declared_attr
    def created_at(cls):
        return mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
            comment="作成日時",
        )

    @declared_attr
    def updated_at(cls):
        return mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
            onupdate=func.now(),
            comment="更新日時",
        )


class DeletableModel(BaseModel):
    """ソフトデリート対応のベースモデル"""

    __abstract__ = True

    @declared_attr
    def deleted_at(cls):
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="削除日時",
        )

    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = func.now()


class UuidMixin:
    uuid: Mapped[UUID] = mapped_column(
        UuidTypeDecorator(),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="UUID",
    )
