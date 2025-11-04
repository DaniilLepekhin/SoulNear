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
from uuid import uuid4
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
    async with db() as session:
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
            personality='coach',
            message_length='brief',
            patterns={'patterns': []},
            insights={'insights': []},
            preferences={}
        )
        session.add(new_profile)
        await session.commit()
        
        # После commit объект все еще в сессии, можем его вернуть
        return new_profile


async def get(user_id: int) -> UserProfile | None:
    """Получить профиль пользователя"""
    async with db() as session:
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
    async with db() as session:
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


async def update_patterns(user_id: int, patterns: list) -> None:
    """
    ЗАМЕНИТЬ паттерны полностью (для работы с Moderate структурой)
    
    Args:
        user_id: Telegram ID пользователя
        patterns: Полный список паттернов (с embeddings)
    """
    async with db() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                patterns={'patterns': patterns},
                updated_at=datetime.utcnow(),
                pattern_analysis_count=UserProfile.pattern_analysis_count + 1,
                last_analysis_at=datetime.utcnow()
            )
        )
        await session.commit()


async def add_patterns(user_id: int, new_patterns: list) -> None:
    """
    Добавить новые паттерны к профилю
    
    Args:
        user_id: Telegram ID пользователя
        new_patterns: Список новых паттернов
    """
    async with db() as session:
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


async def update_insights(user_id: int, insights: list) -> None:
    """
    ЗАМЕНИТЬ инсайты полностью (для работы с Moderate структурой)
    
    Args:
        user_id: Telegram ID пользователя
        insights: Полный список инсайтов
    """
    async with db() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                insights={'insights': insights},
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()


async def add_insights(user_id: int, new_insights: list) -> None:
    """
    Добавить новые инсайты к профилю
    
    Args:
        user_id: Telegram ID пользователя
        new_insights: Список новых инсайтов
    """
    async with db() as session:
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
    async with db() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                preferences=preferences,
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()


async def add_response_hints(user_id: int, hints: list[dict]) -> None:
    """Добавить активные response hints (очередь зеркал для ближайших ответов)."""

    if not hints:
        return

    async with db() as session:
        profile = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )

        if not profile:
            profile = UserProfile(
                user_id=user_id,
                tone_style='friendly',
                personality='coach',
                message_length='brief',
                patterns={'patterns': []},
                insights={'insights': []},
                preferences={}
            )
            session.add(profile)
            await session.flush()

        preferences = dict(profile.preferences or {})
        existing_hints = [
            hint for hint in preferences.get('active_response_hints', [])
            if isinstance(hint, dict)
        ]

        existing_keys = { (hint.get('hint') or '').strip().lower(): hint for hint in existing_hints }

        for hint in hints:
            text = (hint.get('hint') or '').strip()
            if not text:
                continue

            key = text.lower()
            if key in existing_keys:
                # Уже есть такой hint (ещё не использован) — пропускаем
                continue

            prepared_hint = {
                'id': hint.get('id') or str(uuid4()),
                'hint': text,
                'source': hint.get('source') or {},
                'status': hint.get('status') or 'pending',
                'created_at': hint.get('created_at') or datetime.utcnow().isoformat()
            }
            existing_hints.append(prepared_hint)
            existing_keys[key] = prepared_hint

        if not existing_hints:
            # Нечего сохранять
            return

        # Ограничиваем очередь чтобы не раздувалась бесконечно
        preferences['active_response_hints'] = existing_hints[-8:]

        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                preferences=preferences,
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()


async def consume_response_hint(user_id: int, hint_id: str, status: str = 'consumed') -> None:
    """Пометить hint как использованный (по умолчанию удаляет его из очереди)."""

    if not hint_id:
        return

    async with db() as session:
        profile = await session.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )

        if not profile:
            return

        preferences = dict(profile.preferences or {})
        hints = [
            hint for hint in preferences.get('active_response_hints', [])
            if isinstance(hint, dict)
        ]

        if not hints:
            return

        updated_hints = []
        changed = False

        for hint in hints:
            if hint.get('id') == hint_id:
                changed = True
                if status == 'consumed':
                    # Удаляем из очереди
                    continue

                new_hint = dict(hint)
                new_hint['status'] = status
                new_hint['updated_at'] = datetime.utcnow().isoformat()
                updated_hints.append(new_hint)
            else:
                updated_hints.append(hint)

        if not changed:
            return

        preferences['active_response_hints'] = updated_hints

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
    async with db() as session:
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
    async with db() as session:
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(
                insights={'insights': []},
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()

