"""
Logging Configuration Module

This module provides a centralized logging configuration for the application.
It defines standard logging formats and log levels, and offers a utility function
for setting up loggers with consistent configuration across the application.

The module supports configuring log levels via environment variables, allowing
for dynamic adjustment of logging verbosity without code changes.
"""

import logging
import os
import sys

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(name=None):
    """
    Configure and return a logger instance with standardized settings.

    This function sets up a logger with consistent formatting and behavior
    across the application. It configures the logger to output to stdout
    with the application's standard log format and level.

    The log level can be controlled via the LOG_LEVEL environment variable,
    defaulting to INFO if not specified.

    Args:
        name (str, optional): Name for the logger, typically the module name.
                             If None, the root logger is configured.

    Returns:
        Logger: Configured logger instance ready for use

    Example:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Application started")
    """
    # Get the log level from environment variable or use INFO as default
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger
