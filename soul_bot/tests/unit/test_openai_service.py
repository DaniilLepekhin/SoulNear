"""
Unit тесты для OpenAI service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestOpenAIService:
    """Тесты для ChatCompletion API"""
    
    @pytest.mark.asyncio
    async def test_build_system_prompt_basic(self, mock_user):
        """Тест базового system prompt"""
        from bot.services.openai_service import build_system_prompt
        
        profile = {
            'tone_style': 'дружеский',
            'personality': 'наставник',
            'message_length': 'средний',
            'patterns': [],
            'insights': []
        }
        
        prompt = await build_system_prompt(
            user_profile=profile,
            user_data=mock_user,
            assistant_type='helper'
        )
        
        assert 'наставник' in prompt
        assert 'дружеский' in prompt
        assert mock_user['real_name'] in prompt
    
    
    @pytest.mark.asyncio
    async def test_build_system_prompt_with_patterns(self, mock_user):
        """Тест промпта с паттернами"""
        from bot.services.openai_service import build_system_prompt
        
        profile = {
            'tone_style': 'дружеский',
            'personality': 'наставник',
            'message_length': 'средний',
            'patterns': ['Часто говорит о работе', 'Испытывает стресс'],
            'insights': ['Нужна поддержка в карьере']
        }
        
        prompt = await build_system_prompt(
            user_profile=profile,
            user_data=mock_user,
            assistant_type='helper'
        )
        
        assert 'работе' in prompt.lower()
        assert 'стресс' in prompt.lower()
    
    
    @pytest.mark.asyncio
    @patch('bot.services.openai_service.client')
    async def test_get_chat_completion_success(self, mock_client, mock_user, mock_openai_response):
        """Тест успешного запроса к ChatCompletion"""
        from bot.services.openai_service import get_chat_completion
        
        # Мокаем OpenAI ответ
        mock_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(**mock_openai_response)
        )
        
        response = await get_chat_completion(
            user_id=mock_user['user_id'],
            prompt='Привет, как дела?',
            assistant_type='helper',
            include_history=False
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    
    @pytest.mark.asyncio
    async def test_conversation_history_limit(self):
        """Тест лимита истории (не загружаем всё)"""
        from bot.services.openai_service import get_conversation_history
        
        # TODO: реализовать после создания conversation_history таблицы
        pass


class TestPromptBuilder:
    """Тесты для генерации промптов"""
    
    def test_prompt_templates_exist(self):
        """Проверяем, что все шаблоны промптов существуют"""
        from bot.prompts import PROMPTS
        
        required_prompts = [
            'helper_base',
            'sleeper_base',
            'pattern_analysis',
            'quiz_relationships',
            'quiz_money',
            'quiz_purpose'
        ]
        
        for prompt_name in required_prompts:
            assert prompt_name in PROMPTS, f"Промпт {prompt_name} не найден"
    
    
    def test_prompt_variable_substitution(self):
        """Тест подстановки переменных в промпты"""
        from bot.prompts import format_prompt
        
        template = "Привет, {name}! Тебе {age} лет."
        result = format_prompt(template, name="Тест", age=25)
        
        assert result == "Привет, Тест! Тебе 25 лет."

