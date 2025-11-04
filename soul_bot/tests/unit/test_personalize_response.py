import asyncio
from types import SimpleNamespace

import pytest

from bot.services.personalization import build_personalized_response


@pytest.mark.asyncio
async def test_personalize_response_ultra_brief_contains_quote_and_action():
    profile = SimpleNamespace(
        message_length='ultra_brief',
        tone_style='friendly',
        personality='friend',
        patterns={
            'patterns': [
                {
                    'title': 'Imposter Syndrome',
                    'type': 'emotional',
                    'description': 'Feels inadequate despite achievements.',
                    'occurrences': 4,
                    'confidence': 0.88,
                    'evidence': [
                        'Я недостаточно хорош для этой работы.',
                        'Боюсь, что коллеги считают меня самозванцем.'
                    ],
                    'context_weights': {'work': 0.9},
                    'primary_context': 'work',
                    'context_snippets': {
                        'work': ['Я недостаточно хорош для этой работы.'],
                        'self': ['Я недостаточно хорош для этой работы.']
                    }
                }
            ]
        }
    )

    result = await build_personalized_response(
        user_id=123,
        assistant_type='helper',
        profile=profile,
        base_response='Спасибо, что поделился.',
        user_message='Я недостаточно хорош для этой работы.'
    )

    assert '«Я недостаточно хорош для этой работы.»' in result
    assert 'паттерном Imposter Syndrome' in result
    assert '4 раз' in result or '4 раза' in result
    assert 'Сделай шаг:' in result
    assert len(result.split()) <= 50


@pytest.mark.asyncio
async def test_personalize_response_brief_includes_supportive_sentence():
    profile = SimpleNamespace(
        message_length='brief',
        tone_style='sarcastic',
        personality='coach',
        patterns={
            'patterns': [
                {
                    'title': 'Perfectionism',
                    'type': 'behavioral',
                    'description': 'Sets unrealistically high standards.',
                    'occurrences': 6,
                    'confidence': 0.9,
                    'evidence': [
                        'Код должен быть идеальным.',
                        'Я снова переписываю один и тот же модуль.'
                    ],
                    'context_weights': {'work': 1.0},
                    'primary_context': 'work',
                    'context_snippets': {
                        'work': ['Код должен быть идеальным.'],
                        'self': ['Код должен быть идеальным.']
                    }
                }
            ]
        }
    )

    result = await build_personalized_response(
        user_id=456,
        assistant_type='helper',
        profile=profile,
        base_response='Попробуй разбить задачу на этапы.',
        user_message='Код должен быть идеальным.'
    )

    assert '«Код должен быть идеальным.»' in result
    assert 'паттерном Perfectionism' in result
    assert '6 раз' in result or '6 раза' in result
    assert 'Сделай шаг:' in result
    assert 'Сообщи потом, как мир выжил' in result
    assert len(result.split()) <= 120


@pytest.mark.asyncio
async def test_personalize_response_unknown_pattern_uses_fallback_action():
    profile = SimpleNamespace(
        message_length='ultra_brief',
        tone_style='formal',
        personality='coach',
        patterns={
            'patterns': [
                {
                    'title': 'Exotic Pattern',
                    'type': 'cognitive',
                    'description': 'Something unusual.',
                    'occurrences': 1,
                    'confidence': 0.5,
                    'evidence': ['Это что-то новенькое.'],
                    'context_weights': {'self': 1.0},
                    'primary_context': 'self',
                    'context_snippets': {'self': ['Это что-то новенькое.']}
                }
            ]
        }
    )

    result = await build_personalized_response(
        user_id=789,
        assistant_type='helper',
        profile=profile,
        base_response='Интересная ситуация.',
        user_message='Это что-то новенькое.'
    )

    assert '«Это что-то новенькое.»' in result
    assert 'выдели 5 минут на маленький шаг' in result


@pytest.mark.asyncio
async def test_personalize_response_skips_irrelevant_pattern():
    """
    Test that personalization is skipped when pattern is not relevant to current topic.
    
    User has relationship pattern but talks about money → should skip personalization.
    """
    profile = SimpleNamespace(
        message_length='brief',
        tone_style='friendly',
        personality='friend',
        patterns={
            'patterns': [
                {
                    'title': 'Страх потери интереса',
                    'type': 'emotional',
                    'description': 'Боится, что партнер потеряет интерес.',
                    'occurrences': 5,
                    'confidence': 0.8,
                    'evidence': [
                        'Страх быть отвергнутым, непринятым, и собственно, что полностью меня поняв, девушка меня оставит.'
                    ],
                    'context_weights': {
                        'relationships': 1.0,
                        'money': 0.1,  # Very low relevance to money
                        'work': 0.2
                    },
                    'primary_context': 'relationships',
                    'context_snippets': {'relationships': ['Страх быть отвергнутым, непринятым, и собственно, что полностью меня поняв, девушка меня оставит.']}
                }
            ]
        }
    )

    result = await build_personalized_response(
        user_id=999,
        assistant_type='helper',
        profile=profile,
        base_response='Давай разберемся с твоими финансами.',
        user_message='У меня постоянно нет денег'
    )

    # Should NOT mention relationship pattern when talking about money
    assert 'Страх быть отвергнутым' not in result
    assert 'девушка' not in result
    
    # Should return base response (or close to it)
    assert 'финанс' in result.lower() or 'денег' in result.lower() or 'разберемся' in result.lower()

