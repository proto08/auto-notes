from enum import IntEnum
from uuid import UUID

from pydantic import Field

from entities import BaseDto


class TranscribesTaskDto(BaseDto):
    task_id: UUID = Field(description="タスクID")


class TranscribesDto(BaseDto):
    text: str = Field(description="文字起こししたテキスト")
    srt: str = Field(description="SRT形式のテキスト")


class TaskStatus(IntEnum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
