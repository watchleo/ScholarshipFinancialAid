"""Logging setup that writes to both the console and a log file.

[Unit II] File Management: the FileHandler appends every log line to
logs/app.log, giving a permanent audit trail of requests, reviews,
disbursements and errors.
"""

import logging
import os

from config import SETTINGS

_LOGGER_NAME = "scholarship_api"
_configured = False


def configure_logging():
    """Attach console + file handlers to the app logger (run once)."""
    global _configured
    if _configured:
        return

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler - the log folder is created first if missing
    os.makedirs(os.path.dirname(SETTINGS["log_path"]), exist_ok=True)
    file_handler = logging.FileHandler(SETTINGS["log_path"], encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Don't pass records up to the root logger (would duplicate lines)
    logger.propagate = False

    _configured = True
    return logger


def get_logger(name=None):
    """Return a namespaced logger, e.g. scholarship_api.services."""
    configure_logging()
    child = name or "app"
    return logging.getLogger(f"{_LOGGER_NAME}.{child}")
