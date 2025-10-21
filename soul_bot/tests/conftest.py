"""
Фикстуры для pytest
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User

# Тестовая БД (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Создаёт временную БД для тестов"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = async_sessionmaker(engine, expire_on_commit=False)
    
    yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_user():
    """Тестовый пользователь"""
    return {
        'user_id': 123456789,
        'name': 'Test User',
        'username': 'testuser',
        'real_name': 'Тест',
        'age': 25,
        'gender': True,
        'sub_date': datetime.now() + timedelta(days=30)
    }


@pytest.fixture
def mock_openai_response():
    """Мок ответа OpenAI"""
    return {
        'id': 'chatcmpl-test',
        'choices': [{
            'message': {
                'role': 'assistant',
                'content': 'Тестовый ответ от бота'
            },
            'finish_reason': 'stop'
        }],
        'usage': {
            'prompt_tokens': 100,
            'completion_tokens': 50,
            'total_tokens': 150
        }
    }

