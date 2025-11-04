"""Centralized logging configuration for the SoulNear bot."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configure application logging with console + rotating file handlers."""
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "[%(asctime)s][%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y/%m/%d %H:%M:%S",
                },
                "concise": {
                    "format": "[%(asctime)s][%(levelname)s] %(message)s",
                    "datefmt": "%Y/%m/%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "concise",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "filename": str(logs_dir / "bot.log"),
                    "maxBytes": 5_000_000,
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file"],
            },
            "loggers": {
                "bot.services.pattern_analyzer": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "bot.services.quiz_service": {
                    "level": "DEBUG",
                    "handlers": ["file"],
                    "propagate": False,
                },
            },
        }
    )

    logging.getLogger(__name__).debug("Logging configured. Log directory: %s", logs_dir)


