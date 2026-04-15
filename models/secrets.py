from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import Mapped, mapped_column

from models import DeletableModel, UuidMixin


class ApiKey(DeletableModel, UuidMixin):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="APIKEYの持ち主"
    )
    key_hash = mapped_column(LONGBLOB, nullable=False, comment="API KEYのhash")
    is_master: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="マスターキーかどうか"
    )
