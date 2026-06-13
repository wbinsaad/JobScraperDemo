# jobflow_engine/logger.py

import logging
from logging.handlers import RotatingFileHandler
import sys
from typing import Optional

from config import settings

LOG_FILE = "jobflow_engine.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3


def setup_logging(log_level: Optional[str] = None):
    """
    Configure the root logger with console and file handlers.

    Args:
        log_level (Optional[str]): Log level name. Defaults to environment or INFO.
    """
    level = log_level or getattr(settings, "LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    logger.handlers = []  # Clear existing handlers

    # Formatter
    formatter = logging.Formatter(
        fmt="%(levelname)s - %(asctime)s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(numeric_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    fh.setLevel(numeric_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.debug(f"Logging configured. Level: {level}, Output: console + {LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a module-level logger.

    Args:
        name (str): Module name (usually __name__).

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)