"""Logic for tailoring assistant responses using detected patterns."""

from __future__ import annotations

import logging
from typing import List, Optional

from .actions import get_default_actions

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


def _select_primary_pattern(patterns: List[dict]) -> Optional[dict]:
    if not patterns:
        return None

    sorted_patterns = sorted(
        patterns,
        key=lambda item: (
            item.get('occurrences', 0),
            item.get('confidence', 0.0)
        ),
        reverse=True
    )

    for pattern in sorted_patterns:
        evidence = _deduplicate_quotes(pattern.get('evidence', []))
        if evidence:
            pattern = dict(pattern)
            pattern['evidence'] = evidence
            return pattern

    return None


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

    primary_pattern = _select_primary_pattern(patterns)

    if not primary_pattern:
        logger.debug("[%s] personalization skipped: no pattern with evidence", user_id)
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

    if message_length == 'ultra_brief':
        final_message = ' '.join(
            part for part in (quote_sentence, action_sentence) if part
        ).strip()
    else:
        base_sentence = _ensure_period(_extract_first_sentence(base_response))
        supportive_sentence = _ensure_period(_build_supportive_sentence(profile))
        result_parts = [quote_sentence]

        if base_sentence and base_sentence not in quote_sentence:
            result_parts.append(base_sentence)

        result_parts.append(action_sentence)

        if supportive_sentence and supportive_sentence not in action_sentence:
            result_parts.append(supportive_sentence)

        final_message = ' '.join(part for part in result_parts if part).strip()

    logger.debug(
        "[%s] personalization: pattern=%s occurrences=%s quote=%s",
        user_id,
        pattern_title,
        occurrences,
        quote,
    )

    return final_message or base_response


__all__ = ["build_personalized_response"]

