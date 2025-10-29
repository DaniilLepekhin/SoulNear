import asyncio
from types import SimpleNamespace

import pytest

from bot.services.openai_service import _personalize_response


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
                    ]
                }
            ]
        }
    )

    result = await _personalize_response(
        user_id=123,
        assistant_type='helper',
        profile=profile,
        base_response='Спасибо, что поделился.',
        user_message='Я недостаточно хорош для этой работы.'
    )

    assert '"Я недостаточно хорош для этой работы."' in result
    assert '4 раз' in result
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
                    ]
                }
            ]
        }
    )

    result = await _personalize_response(
        user_id=456,
        assistant_type='helper',
        profile=profile,
        base_response='Попробуй разбить задачу на этапы.',
        user_message='Код должен быть идеальным.'
    )

    assert '"Код должен быть идеальным."' in result
    assert '6 раз' in result
    assert 'Сделай шаг:' in result
    assert 'Сообщи потом, как мир выжил' in result
    assert len(result.split()) <= 120

