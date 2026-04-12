import io
from typing import Tuple

from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment, TranscriptionInfo
from sqlalchemy.orm import Session

from services.files import find_file_data

model = WhisperModel(
    "RoachLin/kotoba-whisper-v2.2-faster", device="cpu", compute_type="int8"
)


def transcribe(file_id: int, session: Session) -> str:
    file_bytes = find_file_data(file_id, session)
    text, srt, info = call_whisper(file_bytes)
    return "dummy"


def call_whisper(audio: bytes) -> Tuple[str, str, TranscriptionInfo]:
    segments, info = model.transcribe(
        io.BytesIO(audio),
        language="ja",
        beam_size=5,
        vad_filter=True,
    )
    segments = list[Segment](segments)

    text = "\n".join(segment.text.strip() for segment in segments)
    srt = "\n\n".join(
        f"{i}\n{format_srt_time(segment.start)} --> {format_srt_time(segment.end)}\n{segment.text.strip()}"
        for i, segment in enumerate(segments, start=1)
    )
    return text, srt, info


def format_srt_time(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    ms = (seconds % 1) * 1000
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(ms):03d}"
