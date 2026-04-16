from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import DeletableModel, UuidMixin
from models.files import File
from models.secrets import ApiKey


class Task(DeletableModel, UuidMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="Celery TaskのID"
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("api_keys.id"), nullable=False, comment="APIKEYのID"
    )
    owner: Mapped["ApiKey"] = relationship("ApiKey", back_populates="files")
    file_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"),
        nullable=True,
    )
    file: Mapped[Optional["File"]] = relationship("File", back_populates="tasks")
