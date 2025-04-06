import logging

from app.config import LOG_FORMAT, LOG_LEVEL


def setup_logging():
    """
    Configure application logging.

    Sets up basic logging configuration with the level and format
    defined in app.config.

    Returns:
        logging.Logger: A configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
    )
    return logging.getLogger(__name__)
