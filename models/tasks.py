from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import DeletableModel, UuidMixin
from models.files import File


class Task(DeletableModel, UuidMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    file_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"),
        nullable=True,
    )
    file: Mapped[Optional["File"]] = relationship("File", back_populates="tasks")
