from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import Mapped, mapped_column

from models import DeletableModel, UuidMixin


class ApiKey(DeletableModel, UuidMixin):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="APIKEYの持ち主氏名"
    )
    key_hash = mapped_column(LONGBLOB, nullable=False, comment="API KEYのhash")
    used_counts = mapped_column(Integer, nullable=False, default=0)

    is_master: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="マスターキーかどうか"
    )

    @property
    def is_valid(self) -> bool:
        return self.deleted_at is None and self.key_hash is not None


# TODO: add fingerprinting
# class FingerPrint(DeletableModel, UuidMixin):
#     __tablename__ = "fingerprints"

#     ip: Mapped[str] = mapped_column()
