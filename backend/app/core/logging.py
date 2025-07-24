import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from colorlog import ColoredFormatter

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    color_formatter = ColoredFormatter(
        "%(log_color)s" + LOG_FORMAT,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(color_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str = None) -> logging.Logger:
    import inspect

    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    return logging.getLogger(module.__name__ if module else "__main__")
