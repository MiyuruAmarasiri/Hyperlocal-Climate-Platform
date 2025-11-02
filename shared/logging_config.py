"""Central logging configuration."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from pathlib import Path
from typing import Optional

from .config import get_settings


BASE_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


def configure_logging(level: int = logging.INFO, log_file: Optional[Path] = None) -> None:
    """Configure logging outputs to console and optional rotating file."""

    settings = get_settings()
    logs_dir = settings.logs_dir
    handlers = dict(BASE_LOGGING["handlers"])

    if log_file is not None:
        log_path = logs_dir / log_file
    else:
        log_path = logs_dir / "platform.log"

    handlers["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "standard",
        "level": logging.getLevelName(level),
        "filename": str(log_path),
        "maxBytes": 10 * 1024 * 1024,
        "backupCount": 5,
    }

    config = dict(BASE_LOGGING)
    config["handlers"] = handlers
    config["root"] = {
        "handlers": list(handlers.keys()),
        "level": logging.getLevelName(level),
    }
    dictConfig(config)


__all__ = ["configure_logging"]
