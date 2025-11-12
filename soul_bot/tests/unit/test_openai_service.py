"""Unit-тесты для свежей версии OpenAI сервиса."""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

os.environ.setdefault("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_build_system_prompt_helper_includes_persona(monkeypatch):
    """Проверяем, что system prompt для helper содержит новую персону Soul Near."""
    from bot.services import openai_service

    fake_profile = SimpleNamespace(
        tone_style='friendly',
        personality='coach',
        message_length='brief',
        patterns={'patterns': []},
        insights={'insights': []},
        preferences={'active_response_hints': []},
        emotional_state={},
        learning_preferences={'works_well': [], 'doesnt_work': []},
        custom_instructions=''
        )
        
    fake_user = SimpleNamespace(real_name='Аня', age=28, gender='female')

    monkeypatch.setattr(openai_service.user_profile, 'get_or_create', AsyncMock(return_value=fake_profile))
    monkeypatch.setattr(openai_service.db_user, 'get', AsyncMock(return_value=fake_user))
    monkeypatch.setattr(openai_service.conversation_history, 'get_context', AsyncMock(return_value=[]))

    prompt = await openai_service.build_system_prompt(user_id=42, assistant_type='helper')
        
    assert "Ты — SOUL.near" in prompt
    assert "## 🎨 СТИЛЬ ОБЩЕНИЯ" in prompt
    assert "⚠️ ЭТИ НАСТРОЙКИ СТИЛЯ" in prompt


def test_render_dialogue_state_section_question_phase():
    """Проверяем текст прогресса сессии для блока отношений."""
    from bot.services.openai_service import (
        DIALOGUE_CONFIG,
        _render_dialogue_state_section
    )

    config = DIALOGUE_CONFIG['relationships']
    state = {'questions': 3, 'summary_count': 0, 'final_delivered': False, 'config': config}
    section = _render_dialogue_state_section('relationships', state, expected_role='question')
        
    assert "уже задано вопросов" in section.lower()
    assert "Фаза 1" in section
    assert "Следующий шаг" in section


def test_formatting_structures_helper_response():
    """format_bot_message дробит ответ helper на абзацы и выделяет финальный вопрос."""
    from bot.services.formatting import format_bot_message

    original_text = (
        "Ты сам сказал об этом вчера. Давай сейчас честно: что тебя держит?"
        " Когда ты это проговариваешь, слышится цикл избегания — делаешь шаг и тут же откатываешься."
        " Попробуй назвать один ресурс, который готов поддержать. Что ты выбираешь сделать прямо сейчас?"
    )
    formatted = format_bot_message(
        text=original_text,
        message_length_preference='brief',
        learning_preferences=None,
        assistant_type='helper'
    )

    assert formatted.count('\n\n') >= 1
    assert not formatted.strip().endswith('</b>')
    assert 'Что ты выбираешь сделать прямо сейчас?' in formatted
    assert formatted.count('<b>') <= 2
    assert formatted.count('</b>') == formatted.count('<b>')


def test_format_response_with_headers_keeps_html():
    """format_response_with_headers не должен экранировать готовый HTML."""
    from bot.functions.other import format_response_with_headers

    html_text = "<b>1. Заголовок:</b> это уже оформлено"
    assert format_response_with_headers(html_text) == html_text

