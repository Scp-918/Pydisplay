"""Logging setup for the application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import DEFAULT_LOG_FILE, LOG_DIR


def configure_logging(level: int = logging.INFO) -> None:
    """Configure console and rotating file logging once."""

    root = logging.getLogger()
    if root.handlers:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        DEFAULT_LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)
