"""
Utilities for selecting the most relevant behavioural patterns for the current
conversation context.

The module keeps the logic lightweight (pure Python, no external deps) so it
can be used both in chat responses and quiz generation without pulling in the
pattern analyser itself.  It combines several signals:

- explicit context weights provided by the analyser (`context_weights`)
- tags / primary context collected earlier in the user profile
- freshness (recent detections outrank stale ones)
- plain-text semantic cues from the current user message

The entry-points are `get_relevant_patterns_for_quiz` and
`get_relevant_patterns_for_chat`.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple


TOPIC_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "relationships": (
        "отношен", "партнер", "партнёр", "любов", "близост", "конфликт",
        "ссор", "расставан", "семь", "брак", "ревност", "измен", "довер",
        "секс", "роман", "влюбл"
    ),
    "money": (
        "деньг", "зарплат", "доход", "бюджет", "кредит", "долг",
        "заработ", "инвест", "накоп", "расход", "ипотек", "финанс",
        "оплат", "прибыл", "убыт"
    ),
    "work": (
        "работ", "карьер", "начальн", "коллег", "проект", "задач",
        "дедлайн", "повышен", "увольн", "собеседован", "офис", "команд",
        "бизнес", "стартап", "фриланс"
    ),
    "purpose": (
        "смысл", "предназнач", "цель", "мечт", "призван", "потенциал",
        "мисси", "развит", "рост", "изменен", "будущ", "траект", "вектор"
    ),
    "confidence": (
        "уверен", "самооцен", "самокрит", "сомнен", "стыд", "страх",
        "неудач", "импост", "смелост", "решим"
    ),
    "fears": (
        "боюсь", "страх", "тревог", "паник", "ужас", "волн", "нервн",
        "страшн", "опас", "пережив"
    ),
    "self": (
        "я", "себя", "внутр", "чувств", "эмоци", "настроен", "устал",
        "выгора", "депресс", "энерг"
    ),
}


CATEGORY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "relationships": ("relationships", "relationship", "отношения", "отношение", "love"),
    "money": ("money", "finance", "финансы", "деньги"),
    "work": ("work", "career", "работа", "карьера"),
    "purpose": ("purpose", "meaning", "предназначение", "смысл"),
    "confidence": ("confidence", "уверенность", "self-esteem"),
    "fears": ("fears", "fear", "страхи", "страх", "anxiety", "тревога"),
    "self": ("self", "general", "общий", "default"),
}


UNIVERSAL_PATTERN_HINTS: Tuple[str, ...] = (
    "procrastination",
    "прокрастинац",
    "perfectionism",
    "перфекцион",
    "self-criticism",
    "самокрит",
    "burnout",
    "выгора",
    "imposter",
    "импост",
)


logger = logging.getLogger(__name__)


def _stem(text: str) -> str:
    """Very small stemmer: lowercase + strip Russian endings."""

    text = text.lower()
    if len(text) <= 4:
        return text
    for suffix in ("ами", "ями", "ями", "ами", "ого", "ому", "ими", "ыми", "ого",
                   "ему", "ого", "ой", "ый", "ий", "ое", "ее", "ая", "яя", "ое",
                   "ие", "ые", "ом", "ем", "ах", "ях", "ой", "ей", "ов", "ев",
                   "ов", "ев", "ью", "ся", "ть", "ти", "ие", "ый", "ой", "ий"):
        if text.endswith(suffix) and len(text) - len(suffix) >= 4:
            return text[:-len(suffix)]
    return text


def normalize_topic(topic: str) -> str:
    topic_lower = topic.lower().strip()
    for canonical, aliases in CATEGORY_ALIASES.items():
        if topic_lower in aliases:
            return canonical
    return topic_lower


def detect_topics_from_text(text: str) -> Dict[str, int]:
    stemmed = _stem(text)
    scores: Dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in stemmed)
        if count:
            scores[topic] = count
    return scores


def detect_topic_from_message(message: str) -> str:
    if not message:
        return "self"
    scores = detect_topics_from_text(message.lower())
    if not scores:
        return "self"
    return max(scores, key=scores.get)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _freshness_multiplier(pattern: dict) -> float:
    last_detected = _parse_datetime(pattern.get("last_detected"))
    if not last_detected:
        return 0.7
    days = max(0.0, (datetime.utcnow() - last_detected).days)
    # 1.0 for today, down to ~0.4 after 90 days.
    return max(0.4, math.exp(-days / 90.0))


def _extract_context_weights(pattern: dict) -> Dict[str, float]:
    raw_weights = pattern.get("context_weights") or {}
    normalized: Dict[str, float] = {}
    for raw_key, raw_value in raw_weights.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if value <= 0.0:
            continue
        topic_key = normalize_topic(str(raw_key))
        normalized[topic_key] = max(normalized.get(topic_key, 0.0), value)

    if not normalized:
        return {}

    max_value = max(normalized.values())
    if max_value <= 0.0:
        return {}

    return {topic: min(1.0, value / max_value) for topic, value in normalized.items()}


def _context_weight(pattern: dict, topic: str, *, weights: Optional[Dict[str, float]] = None) -> float:
    topic = normalize_topic(topic)
    if weights is None:
        weights = _extract_context_weights(pattern)
    if topic in weights:
        return weights[topic]
    tags = pattern.get("tags") or []
    normalized_tags = {normalize_topic(tag) for tag in tags if isinstance(tag, str)}
    if topic in normalized_tags:
        return 1.0
    primary = pattern.get("primary_context")
    if primary and normalize_topic(primary) == topic:
        return 1.0
    title = (pattern.get("title") or "").lower()
    if any(hint in title for hint in UNIVERSAL_PATTERN_HINTS):
        return 0.55
    return 0.0


def _semantic_boost(pattern: dict, topic: str, user_message: Optional[str]) -> float:
    if not user_message:
        return 0.0
    topic_keywords = TOPIC_KEYWORDS.get(topic)
    if not topic_keywords:
        return 0.0
    user_lower = user_message.lower()
    if not any(kw in user_lower for kw in topic_keywords):
        return 0.0
    evidence: Iterable[str] = pattern.get("evidence", []) or []
    text_blob = " ".join(str(item) for item in evidence).lower()
    matches = sum(1 for kw in topic_keywords if kw in text_blob)
    if matches == 0:
        description = (pattern.get("description") or "").lower()
        matches = sum(1 for kw in topic_keywords if kw in description)
    if matches == 0:
        return 0.0
    return min(0.35, 0.15 + matches * 0.05)


def _score_pattern(
    pattern: dict,
    topic: str,
    user_message: Optional[str],
    *,
    min_relevance: float,
    strict: bool,
) -> Optional[Tuple[float, float, dict]]:
    canonical_topic = normalize_topic(topic)
    weights = _extract_context_weights(pattern)
    context_value = _context_weight(pattern, canonical_topic, weights=weights)
    semantic = _semantic_boost(pattern, canonical_topic, user_message)
    relevance = max(context_value, semantic)

    snippets = pattern.get("context_snippets") or {}
    has_snippet = bool(snippets.get(canonical_topic))

    max_topic = None
    max_weight = 0.0
    topic_weight = context_value
    if weights:
        max_topic, max_weight = max(weights.items(), key=lambda item: item[1])
        topic_weight = weights.get(canonical_topic, 0.0)

    if strict and not has_snippet and max_topic and max_topic != canonical_topic and (max_weight - topic_weight) >= 0.2 and semantic < 0.3:
        logger.debug(
            "Pattern '%s' skipped for topic '%s': dominant topic '%s' (%.2f > %.2f)",
            pattern.get("title"),
            canonical_topic,
            max_topic,
            max_weight,
            topic_weight,
        )
        return None

    if not has_snippet:
        snippet_threshold = 0.45 if strict else 0.35
        if semantic < 0.25 and context_value < snippet_threshold:
            logger.debug(
                "Pattern '%s' skipped for topic '%s': lacks snippet and weak signal (semantic=%.2f, weight=%.2f)",
                pattern.get("title"),
                canonical_topic,
                semantic,
                context_value,
            )
            return None
        relevance *= 0.7

    if relevance < min_relevance:
        logger.debug(
            "Pattern '%s' skipped for topic '%s': relevance %.2f < threshold %.2f",
            pattern.get("title"),
            canonical_topic,
            relevance,
            min_relevance,
        )
        return None

    occurrences = float(pattern.get("occurrences", 1) or 1)
    occurrences = min(occurrences, 10.0) / 10.0
    confidence = float(pattern.get("confidence", 0.7) or 0.7)
    freshness = _freshness_multiplier(pattern)
    score = relevance * (0.5 + occurrences * 0.2 + confidence * 0.2) * freshness

    return relevance, score, pattern


def filter_patterns_by_relevance(
    patterns: List[dict],
    current_topic: str,
    user_message: Optional[str] = None,
    min_relevance: float = 0.3,
    max_patterns: int = 5,
) -> List[dict]:
    topic = normalize_topic(current_topic)
    scored: List[Tuple[float, float, dict]] = []
    for pattern in patterns or []:
        result = _score_pattern(
            pattern,
            topic,
            user_message,
            min_relevance=min_relevance,
            strict=True,
        )
        if result is not None:
            scored.append(result)

    if not scored:
        # relax threshold slightly as a fallback
        for pattern in patterns or []:
            result = _score_pattern(
                pattern,
                topic,
                user_message,
                min_relevance=max(0.2, min_relevance * 0.75),
                strict=False,
            )
            if result is not None:
                scored.append(result)

    scored.sort(key=lambda item: (item[1], item[0]), reverse=True)
    return [item[2] for item in scored[:max_patterns]]


def get_relevant_patterns_for_quiz(
    patterns: List[dict],
    category: str,
    max_patterns: int = 2,
) -> List[dict]:
    return filter_patterns_by_relevance(
        patterns=patterns,
        current_topic=category,
        user_message=None,
        min_relevance=0.4,
        max_patterns=max_patterns,
    )


def get_relevant_patterns_for_chat(
    patterns: List[dict],
    user_message: str,
    detected_topic: Optional[str] = None,
    max_patterns: int = 5,
) -> List[dict]:
    topic = detected_topic or detect_topic_from_message(user_message)
    return filter_patterns_by_relevance(
        patterns=patterns,
        current_topic=topic,
        user_message=user_message,
        min_relevance=0.3,
        max_patterns=max_patterns,
    )


def merge_context_weights(
    base: Dict[str, float],
    incoming: Dict[str, float],
    weight: float = 1.0,
) -> Dict[str, float]:
    result = dict(base or {})
    for raw_topic, value in (incoming or {}).items():
        topic = normalize_topic(raw_topic)
        try:
            incoming_value = float(value)
        except (TypeError, ValueError):
            continue
        previous = result.get(topic)
        if previous is None:
            result[topic] = incoming_value
        else:
            result[topic] = max(previous, incoming_value * weight)
    return result


def infer_context_weights_from_tags(pattern: dict) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for tag in pattern.get("tags", []) or []:
        topic = normalize_topic(str(tag))
        if topic in TOPIC_KEYWORDS:
            weights[topic] = max(weights.get(topic, 0.0), 1.0)
    primary = pattern.get("primary_context")
    if primary:
        topic = normalize_topic(primary)
        weights[topic] = max(weights.get(topic, 0.0), 1.0)
    return weights


