"""
Repository для работы с историей сообщений (ConversationHistory)

Методы:
- add_message() - добавить сообщение в историю
- get_history() - получить последние N сообщений
- get_context() - получить контекст для ChatCompletion
- count_messages() - посчитать количество сообщений пользователя
- clear_history() - очистить историю (для тестирования)
"""
from datetime import datetime, timedelta
from sqlalchemy import select, delete, desc
from typing import List, Dict

from database.database import db
from database.models.conversation_history import ConversationHistory


async def add_message(
    user_id: int,
    assistant_type: str,
    role: str,
    content: str,
    extra_metadata: dict = None
) -> None:
    """
    Добавить сообщение в историю
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента (helper, sleeper, quiz_relationships, etc.)
        role: Роль (system, user, assistant)
        content: Текст сообщения
        extra_metadata: Дополнительные метаданные (токены, модель, и т.д.)
    """
    async with db() as session:
        message = ConversationHistory(
            user_id=user_id,
            assistant_type=assistant_type,
            role=role,
            content=content,
            extra_metadata=extra_metadata or {},
            timestamp=datetime.utcnow()
        )
        session.add(message)
        await session.commit()


async def get_history(
    user_id: int,
    assistant_type: str,
    limit: int = 50,
    offset: int = 0
) -> List[ConversationHistory]:
    """
    Получить историю сообщений для пользователя и ассистента
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента
        limit: Максимальное количество сообщений
        offset: Сдвиг (для пагинации)
        
    Returns:
        Список объектов ConversationHistory, отсортированных по времени (от старых к новым)
    """
    async with db() as session:
        result = await session.execute(
            select(ConversationHistory)
            .where(
                ConversationHistory.user_id == user_id,
                ConversationHistory.assistant_type == assistant_type
            )
            .order_by(desc(ConversationHistory.timestamp))
            .limit(limit)
            .offset(offset)
        )
        messages = result.scalars().all()
        
        # Возвращаем в обратном порядке (от старых к новым)
        return list(reversed(messages))


async def get_context(
    user_id: int,
    assistant_type: str,
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Получить контекст для ChatCompletion API
    
    Возвращает последние N сообщений в формате для OpenAI:
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента
        max_messages: Максимальное количество сообщений
        
    Returns:
        Список словарей в формате OpenAI
    """
    messages = await get_history(user_id, assistant_type, limit=max_messages)
    
    # Форматируем в формат OpenAI (без system сообщений)
    context = []
    for msg in messages:
        if msg.role != 'system':  # system prompt добавляется отдельно
            context.append({
                'role': msg.role,
                'content': msg.content
            })
    
    return context


async def get_recent_messages_for_analysis(
    user_id: int,
    assistant_type: str,
    limit: int = 20,
    since: datetime = None
) -> List[ConversationHistory]:
    """
    Получить недавние сообщения для анализа паттернов
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента
        limit: Максимальное количество сообщений
        since: Получить сообщения после этой даты
        
    Returns:
        Список объектов ConversationHistory
    """
    async with db() as session:
        query = (
            select(ConversationHistory)
            .where(
                ConversationHistory.user_id == user_id,
                ConversationHistory.assistant_type == assistant_type,
                ConversationHistory.role == 'user'  # Только сообщения пользователя
            )
            .order_by(desc(ConversationHistory.timestamp))
            .limit(limit)
        )
        
        if since:
            query = query.where(ConversationHistory.timestamp >= since)
        
        result = await session.execute(query)
        messages = result.scalars().all()
        
        return list(reversed(messages))


async def count_messages(
    user_id: int,
    assistant_type: str,
    since: datetime = None
) -> int:
    """
    Подсчитать количество сообщений
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента
        since: Подсчитать сообщения после этой даты
        
    Returns:
        Количество сообщений
    """
    async with db() as session:
        from sqlalchemy import func
        
        query = select(func.count(ConversationHistory.id)).where(
            ConversationHistory.user_id == user_id,
            ConversationHistory.assistant_type == assistant_type
        )
        
        if since:
            query = query.where(ConversationHistory.timestamp >= since)
        
        result = await session.scalar(query)
        return result or 0


async def clear_history(
    user_id: int,
    assistant_type: str = None,
    older_than: datetime = None
) -> int:
    """
    Очистить историю сообщений
    
    Args:
        user_id: Telegram ID пользователя
        assistant_type: Тип ассистента (если None, очищает для всех)
        older_than: Удалить сообщения старше этой даты
        
    Returns:
        Количество удалённых сообщений
    """
    async with db() as session:
        query = delete(ConversationHistory).where(
            ConversationHistory.user_id == user_id
        )
        
        if assistant_type:
            query = query.where(ConversationHistory.assistant_type == assistant_type)
        
        if older_than:
            query = query.where(ConversationHistory.timestamp < older_than)
        
        result = await session.execute(query)
        await session.commit()
        
        return result.rowcount


async def cleanup_old_messages(days: int = 30) -> int:
    """
    Очистить старые сообщения для всех пользователей
    
    Args:
        days: Удалить сообщения старше N дней
        
    Returns:
        Количество удалённых сообщений
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    async with db() as session:
        result = await session.execute(
            delete(ConversationHistory)
            .where(ConversationHistory.timestamp < cutoff_date)
        )
        await session.commit()
        
        return result.rowcount

