"""
Repository для работы с QuizSession (Stage 4)

Методы:
- create() - создать новую сессию
- get() - получить сессию по ID
- get_active() - получить активную сессию пользователя
- update_answer() - добавить ответ
- complete() - завершить квиз
- abandon() - пометить как брошенный
- cancel() - отменить квиз
"""
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_
from typing import Optional

from database.database import db
from database.models.quiz_session import QuizSession


async def create(
    user_id: int,
    category: str,
    questions: list[dict],
    source: str = 'menu'
) -> QuizSession:
    """
    Создать новую сессию квиза
    
    Args:
        user_id: ID пользователя
        category: Категория (relationships, work, emotions, etc.)
        questions: Сгенерированные вопросы
        source: Источник запуска (menu, notification, auto_trigger)
        
    Returns:
        QuizSession object
    """
    async with db() as session:
        quiz_session = QuizSession(
            user_id=user_id,
            category=category,
            source=source,
            status='in_progress',
            data={
                "questions": questions,
                "answers": [],
                "current_question_index": 0,
                "total_questions": len(questions)
            }
        )
        
        session.add(quiz_session)
        await session.commit()
        await session.refresh(quiz_session)
        
        return quiz_session


async def get(session_id: int) -> Optional[QuizSession]:
    """
    Получить сессию по ID
    
    Args:
        session_id: ID сессии
        
    Returns:
        QuizSession или None
    """
    async with db() as session:
        result = await session.execute(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        return result.scalar_one_or_none()


async def get_active(user_id: int) -> Optional[QuizSession]:
    """
    Получить активную сессию пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        QuizSession или None
    """
    async with db() as session:
        result = await session.execute(
            select(QuizSession)
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.status == 'in_progress'
                )
            )
            .order_by(QuizSession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def update_answer(
    session_id: int,
    question_id: str,
    answer_value: str
) -> QuizSession:
    """
    Добавить ответ на вопрос
    
    Args:
        session_id: ID сессии
        question_id: ID вопроса
        answer_value: Значение ответа
        
    Returns:
        Обновлённая QuizSession
    """
    async with db() as session:
        # Получаем сессию
        result = await session.execute(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        quiz_session = result.scalar_one()
        
        # Добавляем ответ
        quiz_session.data['answers'].append({
            "question_id": question_id,
            "value": answer_value,
            "answered_at": datetime.now().isoformat()
        })
        
        # Двигаем индекс вперёд
        quiz_session.data['current_question_index'] += 1
        
        # Обновляем last_activity
        quiz_session.last_activity_at = datetime.now()
        
        # Помечаем data как изменённое (для SQLAlchemy JSONB tracking)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(quiz_session, 'data')
        
        await session.commit()
        await session.refresh(quiz_session)
        
        return quiz_session


async def complete(session_id: int, results: dict) -> QuizSession:
    """
    Завершить квиз
    
    Args:
        session_id: ID сессии
        results: Результаты анализа (patterns, insights, recommendations)
        
    Returns:
        Завершённая QuizSession
    """
    async with db() as session:
        quiz_session_obj = await session.get(QuizSession, session_id)
        
        # Вычисляем длительность
        duration = (datetime.now() - quiz_session_obj.created_at).total_seconds()
        
        quiz_session_obj.status = 'completed'
        quiz_session_obj.completed_at = datetime.now()
        quiz_session_obj.duration_seconds = int(duration)
        quiz_session_obj.results = results
        
        await session.commit()
        await session.refresh(quiz_session_obj)
        
        return quiz_session_obj


async def abandon(session_id: int) -> None:
    """
    Пометить квиз как брошенный (timeout)
    
    Args:
        session_id: ID сессии
    """
    async with db() as session:
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(status='abandoned')
        )
        await session.commit()


async def cancel(session_id: int) -> None:
    """
    Отменить квиз (пользователь сам отменил)
    
    Args:
        session_id: ID сессии
    """
    async with db() as session:
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(status='cancelled')
        )
        await session.commit()


async def cleanup_old_sessions(days: int = 30) -> int:
    """
    Удалить старые брошенные/отменённые сессии
    
    Args:
        days: Сколько дней хранить
        
    Returns:
        Количество удалённых сессий
    """
    from sqlalchemy import delete
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    async with db() as session:
        result = await session.execute(
            delete(QuizSession)
            .where(
                and_(
                    QuizSession.status.in_(['abandoned', 'cancelled']),
                    QuizSession.created_at < cutoff_date
                )
            )
        )
        await session.commit()
        
        return result.rowcount


async def check_abandoned_sessions() -> list[QuizSession]:
    """
    Найти зависшие сессии (> 30 минут без активности)
    
    Returns:
        Список зависших сессий
    """
    timeout = datetime.now() - timedelta(minutes=30)
    
    async with db() as session:
        result = await session.execute(
            select(QuizSession)
            .where(
                and_(
                    QuizSession.status == 'in_progress',
                    QuizSession.last_activity_at < timeout
                )
            )
        )
        return list(result.scalars().all())
