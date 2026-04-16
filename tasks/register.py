from uuid import UUID

from sqlalchemy.orm import Session

from entities.errors import NotFoundError
from models.tasks import Task


def find_task(id: int, session: Session):
    task = session.query(Task).filter(Task.id == id, Task.deleted_at.is_(None)).first()
    if not task:
        raise NotFoundError()
    return task


def find_task_by_uuid(uuid: UUID, session: Session):
    task = (
        session.query(Task).filter(Task.uuid == uuid, Task.deleted_at.is_(None)).first()
    )
    if not task:
        raise NotFoundError()
    return task
