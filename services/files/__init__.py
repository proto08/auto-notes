import mimetypes
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from entities.errors import NotFoundError, ValidationError
from models.files import File

FILES_DIR = Path("/tmp/audios")


_WAV_HEADER_LEN = 12
_RIFF = b"RIFF"
_WAVE = b"WAVE"


def is_wav_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            header = f.read(_WAV_HEADER_LEN)
    except OSError:
        return False
    if len(header) < _WAV_HEADER_LEN:
        return False
    return header[:4] == _RIFF and header[8:12] == _WAVE


def ensure_wav_file(path: Path) -> Path:
    if is_wav_file(path):
        return path
    # TODO: convert to wav file
    return path


def save_file(session: Session, data: bytes, suffix: str = "") -> File:
    # 1. save file to docker volume
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    path = FILES_DIR / f"{uuid.uuid4()}{suffix}"
    path.write_bytes(data)

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    # create file model
    model = File(
        path=str(path),
        name=path.name,
        mime_type=mime_type,
        size=len(data),
        duration=None,
    )
    session.add(model)
    session.flush()
    session.refresh(model)
    return model


def find_file_by_uuid(uuid: uuid.UUID, session: Session) -> File:
    file = (
        session.query(File).filter(File.uuid == uuid, File.deleted_at is None).first()
    )
    if file is None:
        raise NotFoundError("File not found")
    return file
