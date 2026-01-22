import logging
import sys
from src.core.config import get_settings

def setup_logger() -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger("bot")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    return logger

logger = setup_logger()
