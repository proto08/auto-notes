from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from entities import BaseDto
from models.files import File


class FileDto(BaseDto):
    uuid: UUID = Field(description="UUID")
    name: str = Field(description="ファイル名")
    mime_type: str = Field(description="MIMEタイプ")
    size: int = Field(description="ファイルサイズ")
    duration: Optional[float] = Field(
        default=None, description="音声の長さ(seconds)"
    )

    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")

    @staticmethod
    def from_model(model: File) -> "FileDto":
        return FileDto(
            uuid=model.uuid,
            name=model.name,
            mime_type=model.mime_type,
            size=model.size,
            duration=model.duration,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
