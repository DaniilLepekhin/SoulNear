"""
Интеграционные тесты для handlers
"""
import pytest
from unittest.mock import AsyncMock, patch
from aiogram.fsm.context import FSMContext


class TestHelperHandler:
    """Тесты для /support (helper) handler"""
    
    @pytest.mark.asyncio
    @patch('bot.handlers.user.helper.check_sub_assistant')
    async def test_support_handler_with_subscription(self, mock_check_sub):
        """Тест обработчика helper при активной подписке"""
        from bot.handlers.user.helper import support
        
        mock_check_sub.return_value = True
        
        # Мокаем callback
        callback = AsyncMock()
        callback.from_user.id = 123456
        callback.message.delete = AsyncMock()
        callback.message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        await support(callback, state)
        
        # Проверяем, что ответ был отправлен
        callback.message.answer.assert_called_once()
        state.set_state.assert_called_once()
    
    
    @pytest.mark.asyncio
    @patch('bot.handlers.user.helper.check_sub_assistant')
    async def test_support_handler_without_subscription(self, mock_check_sub):
        """Тест обработчика helper без подписки"""
        from bot.handlers.user.helper import support
        
        mock_check_sub.return_value = False
        
        callback = AsyncMock()
        callback.from_user.id = 123456
        callback.message.delete = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        await support(callback, state)
        
        # Проверяем, что state НЕ был установлен (нет доступа)
        state.set_state.assert_not_called()


class TestMessageFlow:
    """Тесты полного флоу обработки сообщения"""
    
    @pytest.mark.asyncio
    @patch('bot.functions.other.get_assistant_response')
    @patch('bot.functions.other.check_sub_assistant')
    async def test_text_answer_flow(self, mock_check_sub, mock_get_response):
        """Тест полного флоу текстового ответа"""
        from bot.functions.other import text_answer
        
        mock_check_sub.return_value = True
        mock_get_response.return_value = "Тестовый ответ бота"
        
        # Мокаем message
        message = AsyncMock()
        message.from_user.id = 123456
        message.text = "Привет, бот!"
        message.answer = AsyncMock()
        
        await text_answer(message, assistant='helper')
        
        # Проверяем, что ответ был отправлен
        assert message.answer.call_count >= 1
        mock_get_response.assert_called_once()

