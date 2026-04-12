from uuid import UUID

from pydantic import Field

from entities import BaseDto


class TranscribesTaskDto(BaseDto):
    task_id: UUID = Field(description="タスクID")
