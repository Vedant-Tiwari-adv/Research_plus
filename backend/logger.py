import logging
import os
import time
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler - UTF-8 explicit so special chars work on Windows
    fh = RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(formatter)

    # Console handler - UTF-8 explicit for Windows CP1252 terminals
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.stream = open(os.devnull, 'w') if False else __import__('sys').stdout
    # Force UTF-8 on Windows console
    try:
        ch.stream.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python < 3.7 or non-reconfigurable stream

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


class TimedLogger:
    def __init__(self, logger: logging.Logger, label: str):
        self.logger = logger
        self.label = label
        self.start = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_):
        elapsed = (time.perf_counter() - self.start) * 1000
        # Use ASCII arrow to avoid Windows CP1252 issues
        self.logger.info(f"{self.label} completed in {elapsed:.2f}ms")
        self.elapsed_ms = elapsed