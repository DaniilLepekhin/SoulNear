"""
Repository для работы с профилями пользователей (UserProfile)

Методы:
- get_or_create() - получить или создать профиль
- update_style() - обновить настройки стиля
- add_pattern() - добавить новый паттерн
- add_insight() - добавить новый инсайт
- update_preferences() - обновить предпочтения
"""
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from database.database import db
from database.models.user_profile import UserProfile


async def get_or_create(user_id: int) -> UserProfile:
    """
    Получить профиль пользователя или создать, если не существует
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        UserProfile объект
    """
    async with db.begin() as session:
        # Пытаемся найти существующий профиль
        result = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        
        if result:
            return result
        
        # Если не нашли - создаём новый с дефолтными настройками
        new_profile = UserProfile(
            user_id=user_id,
            tone_style='friendly',
            personality='friend',
            message_length='medium',
            patterns={'patterns': []},
            insights={'insights': []},
            preferences={}
        )
        session.add(new_profile)
        await session.commit()
        await session.refresh(new_profile)
        
        return new_profile


async def get(user_id: int) -> UserProfile | None:
    """Получить профиль пользователя"""
    async with db.begin() as session:
        result = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result


async def update_style(
    user_id: int,
    tone_style: str = None,
    personality: str = None,
    message_length: str = None
) -> None:
    """
    Обновить настройки стиля ответов
    
    Args:
        user_id: Telegram ID пользователя
        tone_style: Тон (formal, friendly, sarcastic, motivating)
        personality: Личность (mentor, friend, coach)
        message_length: Длина (brief, medium, detailed)
    """
    async with db.begin() as session:
        update_data = {'updated_at': datetime.utcnow()}
        
        if tone_style:
            update_data['tone_style'] = tone_style
        if personality:
            update_data['personality'] = personality
        if message_length:
            update_data['message_length'] = message_length
        
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(**update_data)
        )
        await session.commit()


async def add_patterns(user_id: int, new_patterns: list) -> None:
    """
    Добавить новые паттерны к профилю
    
    Args:
        user_id: Telegram ID пользователя
        new_patterns: Список новых паттернов
    """
    async with db.begin() as session:
        profile = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        
        if not profile:
            # Создаём профиль, если его нет
            profile = UserProfile(
                user_id=user_id,
                patterns={'patterns': new_patterns}
            )
            session.add(profile)
        else:
            # Добавляем новые паттерны к существующим
            current_patterns = profile.patterns.get('patterns', [])
            current_patterns.extend(new_patterns)
            
            profile.patterns = {'patterns': current_patterns}
            profile.updated_at = datetime.utcnow()
            profile.pattern_analysis_count += 1
            profile.last_analysis_at = datetime.utcnow()
        
        await session.commit()


async def add_insights(user_id: int, new_insights: list) -> None:
    """
    Добавить новые инсайты к профилю
    
    Args:
        user_id: Telegram ID пользователя
        new_insights: Список новых инсайтов
    """
    async with db.begin() as session:
        profile = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                insights={'insights': new_insights}
            )
            session.add(profile)
        else:
            current_insights = profile.insights.get('insights', [])
            current_insights.extend(new_insights)
            
            profile.insights = {'insights': current_insights}
            profile.updated_at = datetime.utcnow()
        
        await session.commit()


async def update_preferences(user_id: int, preferences: dict) -> None:
    """
    Обновить предпочтения пользователя
    
    Args:
        user_id: Telegram ID пользователя
        preferences: Словарь с предпочтениями
    """
    async with db.begin() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                preferences=preferences,
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()


async def clear_patterns(user_id: int) -> None:
    """Очистить паттерны пользователя (для тестирования)"""
    async with db.begin() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                patterns={'patterns': []},
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()


async def clear_insights(user_id: int) -> None:
    """Очистить инсайты пользователя (для тестирования)"""
    async with db.begin() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                insights={'insights': []},
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()

