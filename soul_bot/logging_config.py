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
                # Настройка логгеров aiogram и других библиотек
                "aiogram": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "aiogram.event": {
                    "level": "WARNING",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "apscheduler": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
            },
        }
    )

    logging.getLogger(__name__).debug("Logging configured. Log directory: %s", logs_dir)

    try:
        from config import ADMIN_CHAT_ID
        if ADMIN_CHAT_ID:
            from bot.services.error_notifier import AdminChatLogHandler

            root_logger = logging.getLogger()
            if not any(isinstance(handler, AdminChatLogHandler) for handler in root_logger.handlers):
                handler = AdminChatLogHandler()
                root_logger.addHandler(handler)
    except Exception as exc:  # pragma: no cover - best effort
        logging.getLogger(__name__).warning("Failed to configure admin log handler: %s", exc)


