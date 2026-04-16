import io
import logging
import re
from typing import Tuple

from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment, TranscriptionInfo
from sqlalchemy.orm import Session

from entities.transcribes import TranscribesDto
from services.files import find_file_data

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info("Loading Whisper model...")
        _model = WhisperModel(
            "RoachLin/kotoba-whisper-v2.2-faster", device="cpu", compute_type="int8"
        )
        logger.info("Whisper model loaded.")
    return _model


def transcribe(file_id: int, session: Session) -> TranscribesDto:
    file_bytes = find_file_data(file_id, session)
    text, srt, info = call_whisper(file_bytes)
    logger.info(f"transcribe successed: {info}")
    clear_text = remove_fillers(text)

    return TranscribesDto(text=clear_text, srt=srt)


def call_whisper(audio: bytes) -> Tuple[str, str, TranscriptionInfo]:
    segments, info = get_model().transcribe(
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


def remove_fillers(text: str) -> str:
    fillers = [
        "えーと",
        "えっと",
        "ええと",
        "えー",
        "ええ",
        "あのー",
        "あのう",
        "あの",
        "うーん",
        "うん",
        "まあ",
        "まー",
        "ま、",
        "そのー",
        "そのう",
        "その",
        "なんか",
        "なんかー",
        "ちょっと",
        "いや",
        "いやー",
        "ほら",
        "ほらー",
        "ねえ",
        "ねー",
        "さあ",
        "さー",
        "ようするに",
        "要するに",
        "つまり",
        "とにかく",
    ]

    fillers.sort(key=len, reverse=True)
    pattern = (
        r"(?<![^\s、。！？])"
        + "("
        + "|".join(map(re.escape, fillers))
        + ")"
        + r"(?=[^\s、。！？]|$)"
    )

    result = re.sub(pattern, "", text)
    result = re.sub(r"  +", " ", result)
    result = result.strip()

    return result
