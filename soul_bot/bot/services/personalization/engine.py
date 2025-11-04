"""Logic for tailoring assistant responses using detected patterns."""

from __future__ import annotations

import logging
from typing import List, Optional

from .actions import get_default_actions
from database.repository import user_profile as user_profile_repo
from bot.services.pattern_context_filter import (
    get_relevant_patterns_for_chat,
    detect_topic_from_message,
)

logger = logging.getLogger(__name__)


def _deduplicate_quotes(quotes: List[str]) -> List[str]:
    """Remove duplicate evidence quotes preserving order."""

    seen = set()
    unique_quotes: List[str] = []

    for quote in quotes or []:
        if not quote:
            continue
        normalized = " ".join(quote.strip().split())
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_quotes.append(normalized)

    return unique_quotes


def _format_occurrence_text(value: Optional[int]) -> str:
    count = int(value or 0)
    if count < 1:
        count = 1

    last_digit = count % 10
    last_two = count % 100

    if last_digit == 1 and last_two != 11:
        suffix = "раз"
    elif last_digit in (2, 3, 4) and last_two not in (12, 13, 14):
        suffix = "раза"
    else:
        suffix = "раз"

    return f"{count} {suffix}"


def _select_action_for_pattern(title: str, pattern_type: Optional[str]) -> str:
    actions = get_default_actions()
    title_key = (title or '').lower()
    for known_key, action in actions.items():
        if known_key in title_key:
            return action

    type_key = (pattern_type or '').lower()
    for known_key, action in actions.items():
        if known_key in type_key:
            return action

    return 'выдели 5 минут на маленький шаг и запиши, что получилось.'


def _extract_first_sentence(text: str) -> str:
    if not text:
        return ""

    stripped = text.strip()
    if not stripped:
        return ""

    for delimiter in ['!', '?']:
        stripped = stripped.replace(f'{delimiter}\n', f'{delimiter} ')

    sentences = [s.strip() for s in stripped.split('.') if s.strip()]
    if sentences:
        return sentences[0]

    return stripped.split('\n')[0]


def _build_supportive_sentence(profile) -> str:
    tone = getattr(profile, 'tone_style', '')
    personality = getattr(profile, 'personality', '')

    if tone == 'sarcastic':
        return 'Сообщи потом, как мир выжил после этого шага.'
    if personality == 'friend' or tone == 'friendly':
        return 'Напиши потом, как это прошло — я рядом.'
    return 'Сообщи позже, как сработает этот шаг.'


def _ensure_period(text: str) -> str:
    if not text:
        return ''

    stripped = text.strip()
    if not stripped:
        return ''

    if stripped[-1] in '.!?':
        return stripped

    return f'{stripped}.'


def _select_primary_pattern(
    patterns: List[dict],
    user_message: str = "",
    detected_topic: Optional[str] = None
) -> Optional[dict]:
    """
    Select the most relevant pattern for personalization.
    
    Strategy:
    1. Filter patterns by context relevance to user's message topic
    2. Among relevant patterns, prefer those with:
       - More occurrences
       - Higher confidence
       - Non-empty evidence
    3. If no relevant patterns, fall back to highest frequency pattern
    
    Args:
        patterns: List of user patterns
        user_message: Current user message for context filtering
        detected_topic: Pre-detected topic (optional, will detect if not provided)
        
    Returns:
        Most relevant pattern with evidence, or None
    """
    if not patterns:
        return None
    
    # 🎯 Step 1: Context-aware filtering if user_message provided
    relevant_patterns = patterns
    if user_message:
        relevant_patterns = get_relevant_patterns_for_chat(
            patterns=patterns,
            user_message=user_message,
            detected_topic=detected_topic,
            max_patterns=5,  # Get top 5 relevant patterns
        )
        
        if relevant_patterns:
            logger.debug(
                f"Context filter: {len(relevant_patterns)}/{len(patterns)} patterns relevant to message"
            )
        else:
            # Fallback: use all patterns if none are contextually relevant
            logger.debug(
                f"Context filter: no relevant patterns found, using all {len(patterns)} patterns"
            )
            relevant_patterns = patterns

    # 🏆 Step 2: Sort by frequency and confidence
    sorted_patterns = sorted(
        relevant_patterns,
        key=lambda item: (
            item.get('occurrences', 0),
            item.get('confidence', 0.0)
        ),
        reverse=True
    )

    # 📝 Step 3: Return first pattern with evidence
    for pattern in sorted_patterns:
        evidence = _deduplicate_quotes(pattern.get('evidence', []))
        if evidence:
            pattern = dict(pattern)
            pattern['evidence'] = evidence
            logger.debug(
                f"Selected pattern: '{pattern.get('title')}' "
                f"(occurrences={pattern.get('occurrences')}, "
                f"confidence={pattern.get('confidence'):.2f})"
            )
            return pattern

    return None


def _is_personalization_relevant(
    user_message: str,
    primary_pattern: dict,
    detected_topic: Optional[str] = None
) -> bool:
    """
    Проверяет релевантность персонализации к текущему сообщению.
    
    Логика (fast heuristic, < 5ms):
    0. Check context_weights: if pattern relevance to topic is low → False
    1. Factual question без эмоций → False (персонализация не нужна)
    2. Pattern keywords присутствуют → True (тема релевантна)
    3. Emotional content → True (всегда персонализируем)
    4. Very short message (< 5 words) → False (скорее всего не эмоционально)
    5. Default → True (conservative: лучше показать, чем пропустить)
    
    Args:
        user_message: Текущее сообщение пользователя
        primary_pattern: Главный паттерн для персонализации
        detected_topic: Pre-detected topic (optional)
        
    Returns:
        True если персонализация релевантна, False если стоит пропустить
        
    Examples:
        >>> _is_personalization_relevant("Какая погода?", {...})
        False  # Factual question
        
        >>> _is_personalization_relevant("Чувствую тревогу", {...})
        True  # Emotional content
        
        >>> _is_personalization_relevant("У меня нет денег", {"context_weights": {"relationships": 1.0, "money": 0.1}})
        False  # Pattern is about relationships, but user talks about money
    """
    if not user_message:
        return False
    
    message_lower = user_message.lower().strip()
    if not message_lower:
        return False
    
    # 🎯 0. Check context_weights: LOW relevance to current topic → skip
    if primary_pattern:
        context_weights = primary_pattern.get('context_weights', {})
        if context_weights:
            # Detect topic if not provided
            topic = detected_topic or detect_topic_from_message(user_message)
            
            if topic:
                relevance = context_weights.get(topic, 0.0)
                
                # If pattern has VERY LOW relevance to current topic → skip
                if relevance < 0.3:
                    logger.debug(
                        f"Personalization skipped: pattern '{primary_pattern.get('title')}' "
                        f"has low relevance ({relevance:.2f}) to topic '{topic}'"
                    )
                    return False
    
    # 1. Emotional content? → ALWAYS relevant (highest priority)
    emotional_keywords = [
        'чувствую', 'грустно', 'тревожно', 'боюсь', 'злюсь',
        'не могу', 'страшно', 'тяжело', 'больно', 'одиноко',
        'устал', 'выгорел', 'паник', 'депресс', 'стресс',
        'переживаю', 'волнуюсь', 'нервничаю', 'расстроен'
    ]
    if any(kw in message_lower for kw in emotional_keywords):
        logger.debug("Personalization relevant: emotional content detected")
        return True
    
    # 2. Pattern keywords present? → relevant (even if factual question)
    if primary_pattern:
        pattern_tags = primary_pattern.get('tags', [])
        pattern_title = primary_pattern.get('title', '').lower()
        
        # Проверяем теги паттерна
        if pattern_tags:
            for tag in pattern_tags:
                if isinstance(tag, str) and tag.lower() in message_lower:
                    logger.debug("Personalization relevant: pattern tag '%s' found", tag)
                    return True
        
        # Проверяем название паттерна (разбиваем на слова)
        if pattern_title:
            # Разбиваем на слова (например "Imposter Syndrome" → ["imposter", "syndrome"])
            title_words = [w for w in pattern_title.split() if len(w) > 3]
            if any(word in message_lower for word in title_words):
                logger.debug("Personalization relevant: pattern title keyword found")
                return True

        # Точное совпадение с evidence — считаем релевантным даже для коротких сообщений
        evidence_entries = primary_pattern.get('evidence', []) or []
        normalized_message = message_lower.strip().strip('"')
        for quote in evidence_entries:
            quote_normalized = quote.lower().strip().strip('"')
            if quote_normalized and quote_normalized == normalized_message:
                logger.debug("Personalization relevant: message matches evidence quote")
                return True
    
    # 3. Factual questions WITHOUT emotions or pattern keywords → skip
    factual_indicators = [
        'какая', 'какой', 'какое', 'сколько', 'когда', 'где',
        'кто', 'что такое', 'как называется', 'почему', 'зачем',
        'можешь', 'можно ли', 'как сделать'
    ]
    
    has_question_mark = '?' in user_message
    has_factual_indicator = any(ind in message_lower for ind in factual_indicators)
    
    if has_question_mark and has_factual_indicator:
        logger.debug("Skipping personalization: factual question without emotions/keywords")
        return False
    
    # 4. Very short message (< 5 words) → probably not emotional
    word_count = len(user_message.split())
    if word_count < 5:
        logger.debug("Skipping personalization: message too short (%d words)", word_count)
        return False
    
    # 5. Default: apply personalization (conservative approach)
    logger.debug("Personalization relevant: default (conservative)")
    return True


async def build_personalized_response(
    *,
    user_id: int,
    assistant_type: str,
    profile,
    base_response: str,
    user_message: str,
) -> str:
    """Construct short personalized answer using detected patterns."""

    try:
        patterns_data = getattr(profile, 'patterns', {}) or {}
        patterns: List[dict] = patterns_data.get('patterns', []) if isinstance(patterns_data, dict) else []
    except Exception:  # pragma: no cover - defensive fallback
        logger.debug("[%s] personalization skipped: invalid profile", user_id)
        return base_response

    preferences = getattr(profile, 'preferences', {}) if profile else {}
    active_hints = []
    if isinstance(preferences, dict):
        raw_hints = preferences.get('active_response_hints') or []
        if isinstance(raw_hints, list):
            active_hints = [hint for hint in raw_hints if isinstance(hint, dict)]

    # 🎯 Detect topic once for both pattern selection and relevance check
    detected_topic = detect_topic_from_message(user_message) if user_message else None
    
    # 🔥 Select pattern using context-aware filtering
    primary_pattern = _select_primary_pattern(
        patterns=patterns,
        user_message=user_message,
        detected_topic=detected_topic
    )

    if not primary_pattern:
        logger.debug("[%s] personalization skipped: no pattern with evidence", user_id)
        return base_response
    
    # 🔥 Check if personalization is relevant to current message
    is_relevant = _is_personalization_relevant(
        user_message=user_message,
        primary_pattern=primary_pattern,
        detected_topic=detected_topic
    )
    
    pending_hint = None
    for hint in active_hints:
        status = hint.get('status', 'pending')
        if status in (None, 'pending'):
            pending_hint = hint
            break

    if not is_relevant and pending_hint is None:
        logger.debug("[%s] personalization skipped: not relevant to current message", user_id)
        return base_response

    evidence_list = primary_pattern['evidence']
    quote = evidence_list[0]

    occurrences = primary_pattern.get('occurrences', len(evidence_list))
    occurrences_text = _format_occurrence_text(occurrences)
    pattern_title = primary_pattern.get('title') or 'выявленного паттерна'

    quote_sentence = _ensure_period(
        f'Ты писал: "{quote}" — ты повторял это {occurrences_text}. Это проявление {pattern_title}.'
    )
    action_sentence = _ensure_period(
        f'Сделай шаг: {_select_action_for_pattern(pattern_title, primary_pattern.get("type"))}'
    )

    message_length = getattr(profile, 'message_length', 'brief')

    hint_sentence = None
    hint_id = None
    if pending_hint:
        text = (pending_hint.get('hint') or '').strip()
        if text:
            hint_sentence = _ensure_period(text)
            hint_id = pending_hint.get('id')

    if message_length == 'ultra_brief':
        parts = []
        if hint_sentence:
            parts.append(hint_sentence)
        for part in (quote_sentence, action_sentence):
            if part and part not in parts:
                parts.append(part)
        final_message = ' '.join(parts).strip()
    else:
        base_sentence = _ensure_period(_extract_first_sentence(base_response))
        supportive_sentence = _ensure_period(_build_supportive_sentence(profile))
        result_parts = []

        if hint_sentence:
            result_parts.append(hint_sentence)

        if quote_sentence:
            result_parts.append(quote_sentence)

        if base_sentence and base_sentence not in result_parts:
            result_parts.append(base_sentence)

        if action_sentence:
            result_parts.append(action_sentence)

        if supportive_sentence and supportive_sentence not in result_parts:
            result_parts.append(supportive_sentence)

        final_message = ' '.join(part for part in result_parts if part).strip()

    logger.debug(
        "[%s] personalization: pattern=%s occurrences=%s quote=%s",
        user_id,
        pattern_title,
        occurrences,
        quote,
    )

    if hint_id:
        try:
            await user_profile_repo.consume_response_hint(user_id, hint_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("[%s] failed to consume response hint %s: %s", user_id, hint_id, exc)

    return final_message or base_response


__all__ = ["build_personalized_response"]

