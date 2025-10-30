"""Default behavioral actions mapped from detected pattern titles."""

from __future__ import annotations

from typing import Dict

DEFAULT_ACTIONS: Dict[str, str] = {
    "imposter syndrome": "запиши одно достижение за сегодня и поделись им с коллегой или в заметках.",
    "perfectionism": "выдели 10 минут на черновик без правок — просто зафиксируй прогресс и остановись.",
    "social anxiety in professional settings": "сформулируй один вопрос и отправь его коллеге сегодня, даже если он кажется простым.",
    "procrastination through over-analysis": "запусти таймер на 5 минут и сделай первую часть задачи без оценки результата.",
    "negative self-talk": "перепиши мысль в поддерживающем ключе и проговори новую формулировку вслух.",
}


def get_default_actions() -> Dict[str, str]:
    """Return base mapping of pattern keywords to recommended actions."""

    return DEFAULT_ACTIONS.copy()


__all__ = ["get_default_actions"]



