import tempfile
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock


@contextmanager
def semaphore(name: str):
    lock_file = Path(tempfile.gettempdir()).joinpath(f"{name}.lock")
    lock = FileLock(lock_file.as_posix())
    with lock:
        yield
