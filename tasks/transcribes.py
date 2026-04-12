from tasks import app


@app.task
def transcribe_audio_task(self, file_id: int):
    # trigger transcribes task
    pass
