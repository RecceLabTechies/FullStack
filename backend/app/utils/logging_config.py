import logging
from app.config import LOG_LEVEL, LOG_FORMAT


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
    )
    return logging.getLogger(__name__)
