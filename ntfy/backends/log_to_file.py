from pathlib import Path
from datetime import datetime


def notify(title, message, log_path: Path, retcode=None):
    log_path = Path(log_path).expanduser()
    log_path.touch()

    with open(log_path, "a") as log_file:
        log_file.write(f"{datetime.now()}: {title=} {message=}\n")
