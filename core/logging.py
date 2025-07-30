import logging
import sys
from enum import StrEnum

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def configure_logging(log_level: str = LogLevel.INFO) -> None:
    level = log_level.upper()
    if level not in LogLevel:
        level = LogLevel.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logging.basicConfig(level=level, handlers=[handler])

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = get_logger(__name__)
    logger.info(f"Logging configured with level: {level}")