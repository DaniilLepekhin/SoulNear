"""Public API for personalization helpers.

The personalization engine depends on configuration that pulls secrets from the
environment.  During unit tests we may not have real secrets available, so we
seed harmless defaults before importing the heavy module.  Production
deployments already define proper environment variables and the defaults below
are ignored thanks to ``setdefault``.
"""

from __future__ import annotations

import os

_REQUIRED_ENV_DEFAULTS = {
    "BOT_TOKEN": "test-bot-token",
    "OPENAI_API_KEY": "test-openai-key",
    "POSTGRES_PASSWORD": "test-password",
    "POSTGRES_DB": "test-db",
}

for _env_key, _env_value in _REQUIRED_ENV_DEFAULTS.items():
    os.environ.setdefault(_env_key, _env_value)

from .engine import build_personalized_response  # noqa: E402  (import after env setup)

__all__ = ["build_personalized_response"]

