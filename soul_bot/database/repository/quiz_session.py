"""
Repository для работы с QuizSession

CRUD operations + business logic queries
"""
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, and_
from sqlalchemy.orm import Session

from database.database import db
from database.models.quiz_session import QuizSession

logger = logging.getLogger(__name__)


async def create(
    user_id: int,
    category: str,
    assistant_type: str = 'helper',
    questions: list = None
) -> QuizSession:
    """
    Создать новую quiz session
    
    Args:
        user_id: ID пользователя
        category: Категория квиза (relationships, money, confidence, fears)
        assistant_type: Тип ассистента
        questions: Pre-generated questions (optional)
        
    Returns:
        Created QuizSession
    """
    async with db() as session:
        quiz = QuizSession(
            user_id=user_id,
            category=category,
            assistant_type=assistant_type,
            questions=questions or [],
            answers=[],
            total_questions=len(questions) if questions else None
        )
        
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)
        
        logger.info(f"Created quiz session: user={user_id}, category={category}, id={quiz.id}")
        
        return quiz


async def get(quiz_id: int) -> Optional[QuizSession]:
    """Получить quiz session по ID"""
    async with db() as session:
        result = await session.execute(
            select(QuizSession).where(QuizSession.id == quiz_id)
        )
        return result.scalar_one_or_none()


async def get_active(
    user_id: int,
    assistant_type: str = 'helper'
) -> Optional[QuizSession]:
    """
    Получить активную (in_progress) quiz session пользователя
    
    Returns:
        Active QuizSession or None
    """
    async with db() as session:
        result = await session.execute(
            select(QuizSession)
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.assistant_type == assistant_type,
                    QuizSession.status == 'in_progress'
                )
            )
            .order_by(QuizSession.created_at.desc())
        )
        return result.scalar_one_or_none()


async def get_user_sessions(
    user_id: int,
    limit: int = 10,
    category: str = None,
    status: str = None
) -> List[QuizSession]:
    """
    Получить quiz sessions пользователя
    
    Args:
        user_id: ID пользователя
        limit: Максимальное количество результатов
        category: Фильтр по категории (optional)
        status: Фильтр по статусу (optional)
        
    Returns:
        List of QuizSession (sorted by created_at DESC)
    """
    async with db() as session:
        query = select(QuizSession).where(QuizSession.user_id == user_id)
        
        if category:
            query = query.where(QuizSession.category == category)
        
        if status:
            query = query.where(QuizSession.status == status)
        
        query = query.order_by(QuizSession.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())


async def update_answer(
    session_id: int,
    question_id: str,
    answer_value: str
) -> QuizSession:
    """
    Добавить ответ к quiz session и increment question index
    
    Args:
        session_id: ID quiz session
        question_id: ID вопроса
        answer_value: Значение ответа
        
    Returns:
        Updated QuizSession
    """
    async with db() as session:
        # Получаем quiz
        quiz = await session.get(QuizSession, session_id)
        if not quiz:
            raise ValueError(f"Quiz session {session_id} not found")
        
        # Добавляем ответ
        answers = quiz.answers or []
        answers.append({
            'question_id': question_id,
            'value': answer_value,
            'answered_at': datetime.utcnow().isoformat()
        })
        
        # Обновляем quiz
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(
                answers=answers,
                current_question_index=quiz.current_question_index + 1,
                updated_at=datetime.utcnow()
            )
        )
        
        await session.commit()
        
        # Refresh and return
        await session.refresh(quiz)
        
        logger.info(f"Added answer to quiz {session_id}: question={question_id}, progress={quiz.current_question_index}/{quiz.total_questions}")
        
        return quiz


async def add_answer(
    quiz_id: int,
    answer: str,
    question_id: int = None
) -> QuizSession:
    """
    DEPRECATED: Use update_answer() instead
    Добавить ответ к quiz session
    
    Args:
        quiz_id: ID quiz session
        answer: Ответ пользователя
        question_id: ID вопроса (optional, defaults to current_question_index)
        
    Returns:
        Updated QuizSession
    """
    return await update_answer(quiz_id, str(question_id or 0), answer)


async def update_status(
    quiz_id: int,
    status: str,
    completed_at: datetime = None
) -> QuizSession:
    """
    Обновить статус quiz session
    
    Args:
        quiz_id: ID quiz session
        status: Новый статус (in_progress, completed, cancelled)
        completed_at: Время завершения (для status=completed)
        
    Returns:
        Updated QuizSession
    """
    async with db() as session:
        values = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if status == 'completed' and completed_at:
            values['completed_at'] = completed_at
        
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == quiz_id)
            .values(**values)
        )
        
        await session.commit()
        
        # Get and return updated quiz
        quiz = await session.get(QuizSession, quiz_id)
        
        logger.info(f"Updated quiz {quiz_id} status: {status}")
        
        return quiz


async def update_results(
    quiz_id: int,
    patterns: list = None,
    insights: list = None,
    recommendations: list = None
) -> QuizSession:
    """
    Обновить результаты анализа quiz
    
    Args:
        quiz_id: ID quiz session
        patterns: Extracted patterns
        insights: Generated insights
        recommendations: Actionable recommendations
        
    Returns:
        Updated QuizSession
    """
    async with db() as session:
        values = {'updated_at': datetime.utcnow()}
        
        if patterns is not None:
            values['patterns'] = patterns
        
        if insights is not None:
            values['insights'] = insights
        
        if recommendations is not None:
            values['recommendations'] = recommendations
        
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == quiz_id)
            .values(**values)
        )
        
        await session.commit()
        
        # Get and return updated quiz
        quiz = await session.get(QuizSession, quiz_id)
        
        logger.info(f"Updated quiz {quiz_id} results: patterns={len(patterns or [])}, insights={len(insights or [])}")
        
        return quiz


async def delete(quiz_id: int) -> bool:
    """
    Удалить quiz session
    
    Args:
        quiz_id: ID quiz session
        
    Returns:
        True if deleted, False if not found
    """
    async with db() as session:
        quiz = await session.get(QuizSession, quiz_id)
        
        if not quiz:
            return False
        
        await session.delete(quiz)
        await session.commit()
        
        logger.info(f"Deleted quiz session: {quiz_id}")
        
        return True


async def complete(
    quiz_id: int,
    results: dict = None
) -> QuizSession:
    """
    Завершить квиз (set status=completed, save results)
    
    Args:
        quiz_id: ID quiz session
        results: Analysis results (patterns, insights, recommendations)
        
    Returns:
        Updated QuizSession
    """
    async with db() as session:
        values = {
            'status': 'completed',
            'completed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Сохраняем результаты если есть
        if results:
            if 'new_patterns' in results:
                values['patterns'] = results['new_patterns']
            if 'insights' in results:
                values['insights'] = results.get('insights', [])
            if 'recommendations' in results:
                values['recommendations'] = results['recommendations']
        
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == quiz_id)
            .values(**values)
        )
        
        await session.commit()
        
        # Get and return
        quiz = await session.get(QuizSession, quiz_id)
        
        logger.info(f"Completed quiz {quiz_id}")
        
        return quiz


async def cancel(
    quiz_id: int
) -> QuizSession:
    """
    Отменить квиз (set status=cancelled)
    
    Args:
        quiz_id: ID quiz session
        
    Returns:
        Updated QuizSession
    """
    return await update_status(quiz_id, 'cancelled')


async def get_statistics(user_id: int) -> dict:
    """
    Получить статистику quiz sessions пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Statistics dict
    """
    sessions = await get_user_sessions(user_id, limit=100)
    
    total = len(sessions)
    completed = len([s for s in sessions if s.status == 'completed'])
    in_progress = len([s for s in sessions if s.status == 'in_progress'])
    cancelled = len([s for s in sessions if s.status == 'cancelled'])
    
    categories = {}
    for session in sessions:
        if session.category not in categories:
            categories[session.category] = 0
        categories[session.category] += 1
    
    return {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'cancelled': cancelled,
        'completion_rate': (completed / total * 100) if total > 0 else 0,
        'categories': categories
    }
