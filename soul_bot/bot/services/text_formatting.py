"""\
Вспомогательные функции форматирования для текстовых шаблонов.

Содержит: стихийное обрезание строк без троеточий и локализацию
названий паттернов/типов.
"""

from __future__ import annotations

import re
from typing import Optional


_SENTENCE_ENDINGS = (".", "!", "?")
_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")


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
    "commitment anxiety": "Страх обязательств",
    "emotional walls": "Эмоциональные стены",
    "people pleasing loop": "Петля угождения",
    "scarcity mindset": "Сценарий нехватки",
    "financial guilt": "Вина за деньги",
    "control loop": "Контроль во вред себе",
    "fear of intimacy": "Страх близости",
    "avoidant attachment": "Избегающая привязанность",
    "anxious attachment": "Тревожная привязанность",
    "imposter loop": "Петля самозванца",
    "perfection loop": "Петля перфекционизма",
    "perfection spiral": "Спираль перфекционизма",
}


_PATTERN_TYPE_TRANSLATIONS = {
    "behavioral": "поведенческий",
    "emotional": "эмоциональный",
    "cognitive": "когнитивный",
}


_TOPIC_EMOJI_MAP = {
    "relationships": "🤍",
    "money": "💸",
    "purpose": "🌿",
    "confidence": "☁️",
    "fears": "🧩",
    "sleep": "🌙",
    "dreams": "🌙",
    "stress": "☁️",
    "self": "🧩",
    "work": "🧩",
    "chat": "💬",
    "communication": "💬",
    "practices": "🪷",
    "video": "🎥",
}


def safe_shorten(text: Optional[str], limit: int = 160) -> str:
    """
    Возвращает текст, обрезанный без обрывов предложений и троеточий.
    
    Если текст превышает лимит, но не превышает лимит * 1.5, возвращает его полностью,
    чтобы сохранить целостность предложений. Это предотвращает обрывы в середине фраз.
    """

    if not text:
        return ""

    normalized = " ".join(text.strip().split())
    
    # Мягкий лимит: если текст не превышает лимит в 1.5 раза, возвращаем полностью
    soft_limit = int(limit * 1.5)
    if len(normalized) <= soft_limit:
        return normalized
    
    # Если текст слишком длинный, применяем строгий лимит с обрезкой по предложениям
    sentences = _SENTENCE_SPLIT_REGEX.split(normalized)
    
    # Если только одно предложение и оно не превышает мягкий лимит, возвращаем полностью
    non_empty_sentences = [s.strip() for s in sentences if s.strip()]
    if len(non_empty_sentences) == 1 and len(non_empty_sentences[0]) <= soft_limit:
        return normalized

    collected: list[str] = []
    current_length = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        proposed_length = current_length + (1 if collected else 0) + len(sentence)
        if proposed_length <= limit:
            collected.append(sentence)
            current_length = proposed_length
        else:
            # Если предложение не помещается, но оно одно и не превышает мягкий лимит, возвращаем его
            if not collected and len(sentence) <= soft_limit:
                return sentence
            break

    if collected:
        result = " ".join(collected).strip()
        # Если результат заканчивается знаком, возвращаем как есть
        if result.endswith(_SENTENCE_ENDINGS):
            return result

        # Попробуем укоротить до последнего знака окончания предложения внутри
        for index in range(len(result) - 1, -1, -1):
            if result[index] in _SENTENCE_ENDINGS:
                candidate = result[: index + 1].strip()
                if candidate:
                    return candidate

    cutoff = normalized[:limit].rstrip()

    for index in range(len(cutoff) - 1, -1, -1):
        if cutoff[index] in _SENTENCE_ENDINGS:
            candidate = cutoff[: index + 1].strip()
            if candidate:
                return candidate

    if " " in cutoff:
        candidate = cutoff.rsplit(" ", 1)[0].strip()
        if candidate:
            return candidate.rstrip(",;:-")

    return cutoff.rstrip(",;:-")


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


def get_topic_emoji(topic: Optional[str], fallback: str = "🧩") -> str:
    """Возвращает аккуратный эмодзи по теме/категории."""

    if not topic:
        return fallback

    normalized = str(topic).lower().strip()
    return _TOPIC_EMOJI_MAP.get(normalized, fallback)


