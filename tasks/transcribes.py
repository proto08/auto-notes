import logging

from base.databases import session_context
from base.multitask import semaphore
from services.transcribes import transcribe
from tasks import app

logger = logging.getLogger(__name__)


@app.task(bind=True)
def transcribe_task(self, file_id: int):
    with semaphore("transcribe_task"):
        with session_context() as session:
            _ = transcribe(file_id, session)
            logger.info(f"transcribed {file_id}")
            pass
    pass
