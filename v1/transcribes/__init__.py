from pathlib import Path
from typing import Annotated
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from base.databases import create_session
from entities import TypedResponse
from entities.files import FileDto
from entities.transcribes import TranscribesTaskDto
from services.files import find_file_by_uuid, save_file
from tasks.transcribes import transcribe_task

router = APIRouter()


@router.post("/uploads", response_model=TypedResponse[FileDto])
async def upload(
    upload_file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(create_session)],
):
    data = await upload_file.read()
    suffix = Path(upload_file.filename).suffix if upload_file.filename else ""
    file = save_file(session, data, suffix)
    session.commit()
    return TypedResponse[FileDto](item=FileDto.from_model(file))


@router.post("/{uuid}", response_model=TypedResponse[TranscribesTaskDto])
async def transcribe(
    uuid: UUID,
    session: Annotated[Session, Depends(create_session)],
):
    file = find_file_by_uuid(uuid, session)
    result: AsyncResult = transcribe_task.delay(file.id)
    # TODO: create task
    return TypedResponse[TranscribesTaskDto](
        item=TranscribesTaskDto(task_id=UUID(result.id))
    )


@router.get("/tasks/{uuid}")
async def get(uuid: UUID, session: Annotated[Session, Depends(create_session)]):
    # get task id and status from model. if success, return result.

    pass
