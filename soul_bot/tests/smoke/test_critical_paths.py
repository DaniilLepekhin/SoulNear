"""
Smoke тесты критических путей
Запускаются перед каждым деплоем
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestCriticalPaths:
    """Smoke тесты самых важных флоу"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Проверка подключения к БД"""
        from database.database import db
        
        async with db.begin() as session:
            # Если упадёт — БД недоступна
            result = await session.execute("SELECT 1")
            assert result is not None
    
    
    @pytest.mark.asyncio
    async def test_user_creation(self, test_db):
        """Тест создания пользователя"""
        import database.repository.user as db_user
        from datetime import datetime
        
        user_id = 999999999
        
        await db_user.new(
            user_id=user_id,
            name='Test',
            username='test',
            ref=None,
            sub_date=datetime.now()
        )
        
        user = await db_user.get(user_id=user_id)
        assert user is not None
        assert user.user_id == user_id
    
    
    @pytest.mark.asyncio
    @patch('bot.functions.ChatGPT.client')
    async def test_openai_connection(self, mock_client):
        """Проверка подключения к OpenAI (мок)"""
        from bot.functions.ChatGPT import get_assistant_response
        
        mock_client.beta.threads.create = AsyncMock(
            return_value=AsyncMock(id='thread_test123')
        )
        mock_client.beta.threads.messages.create = AsyncMock()
        mock_client.beta.threads.runs.create_and_poll = AsyncMock(
            return_value=AsyncMock(status='completed', id='run_123')
        )
        mock_client.beta.threads.messages.list = AsyncMock(
            return_value=AsyncMock(
                data=[
                    AsyncMock(
                        role='assistant',
                        content=[AsyncMock(text=AsyncMock(value='Test response'))]
                    )
                ]
            )
        )
        
        # Должен пройти без ошибок
        response = await get_assistant_response(
            user_id=123456,
            prompt='Test',
            assistant='helper'
        )
        
        assert response is not None


class TestMigrationCompatibility:
    """Тесты совместимости старого и нового кода"""
    
    @pytest.mark.asyncio
    @patch('config.USE_CHAT_COMPLETION', False)
    async def test_old_api_still_works(self):
        """Проверка, что старый Assistant API код работает"""
        # TODO: реализовать после feature flag
        pass
    
    
    @pytest.mark.asyncio
    @patch('config.USE_CHAT_COMPLETION', True)
    async def test_new_api_works(self):
        """Проверка, что новый ChatCompletion код работает"""
        # TODO: реализовать после миграции
        pass

