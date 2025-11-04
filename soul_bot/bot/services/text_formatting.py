"""\
Вспомогательные функции форматирования для текстовых шаблонов.

Содержит: стихийное обрезание строк без троеточий и локализацию
названий паттернов/типов.
"""

from __future__ import annotations

from typing import Optional


_SENTENCE_ENDINGS = (".", "!", "?")


_PATTERN_TITLE_TRANSLATIONS = {
    "depression": "Депрессия",
    "burnout": "Эмоциональное выгорание",
    "perfectionism": "Перфекционизм",
    "imposter syndrome": "Синдром самозванца",
    "financial anxiety": "Финансовая тревога",
    "relationship anxiety": "Тревога в отношениях",
    "people pleasing": "Страх отказать",
    "abandonment fear": "Страх быть брошенным",
    "loneliness loop": "Петля одиночества",
    "fear of failure": "Страх неудачи",
    "self criticism": "Самокритика",
    "self-criticism": "Самокритика",
    "social anxiety": "Социальная тревожность",
    "confidence gap": "Провал в уверенности",
    "control issues": "Потребность всё контролировать",
    "avoidant coping": "Избегающее поведение",
    "emotional numbness": "Эмоциональное онемение",
    "sleepless stress": "Бессонный стресс",
    "parent wound": "Родительская травма",
    "money guilt": "Вина за деньги",
    "overthinking": "Руминация",
    "panic spikes": "Приступы паники",
    "grief loop": "Цикл проживание горя",
    "trust issues": "Недоверие",
    "fear of success": "Страх успеха",
    "people-pleasing": "Страх отказать",
    "procrastination": "Прокрастинация",
    "hyper-independence": "Гипернезависимость",
}


_PATTERN_TYPE_TRANSLATIONS = {
    "behavioral": "поведенческий",
    "emotional": "эмоциональный",
    "cognitive": "когнитивный",
}


def safe_shorten(text: Optional[str], limit: int = 160) -> str:
    """Возвращает текст, обрезанный без обрывов предложений и троеточий."""

    if not text:
        return ""

    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized

    cutoff = normalized[:limit]

    # Пытаемся сохранить полное предложение
    for index in range(len(cutoff) - 1, -1, -1):
        if cutoff[index] in _SENTENCE_ENDINGS:
            candidate = cutoff[: index + 1].strip()
            if candidate:
                return candidate

    # Иначе обрезаем по последнему пробелу
    if " " in cutoff:
        candidate = cutoff.rsplit(" ", 1)[0].strip()
        if candidate:
            return candidate

    return cutoff.strip()


def localize_pattern_title(title: Optional[str]) -> str:
    """Приводит название паттерна к русскому эквиваленту."""

    if not title:
        return "Паттерн"

    normalized = title.strip()
    translation = _PATTERN_TITLE_TRANSLATIONS.get(normalized.lower())
    if translation:
        return translation

    return normalized


def localize_pattern_type(pattern_type: Optional[str]) -> str:
    """Возвращает русское название типа паттерна."""

    if not pattern_type:
        return ""

    translation = _PATTERN_TYPE_TRANSLATIONS.get(pattern_type.lower())
    if translation:
        return translation

    return pattern_type


