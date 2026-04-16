from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import DeletableModel, UuidMixin
from models.secrets import ApiKey


class File(DeletableModel, UuidMixin):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("api_keys.id"), nullable=False, comment="APIKEYのID"
    )
    owner: Mapped["ApiKey"] = relationship("ApiKey", back_populates="files")
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(
        Numeric[Decimal](precision=10, scale=2),
        nullable=True,
        comment="音声の長さ(seconds)",
    )
