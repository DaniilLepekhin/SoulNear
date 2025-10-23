"""
Repository для работы с сессиями квизов (QuizSession)

Методы:
- create() - создать новую сессию квиза
- get_active() - получить активную (незавершённую) сессию
- add_answer() - добавить ответ на вопрос
- complete() - завершить квиз и сохранить инсайты
- get_completed() - получить завершённые квизы пользователя
"""
from datetime import datetime
from sqlalchemy import select, update, and_
from typing import List

from database.database import db
from database.models.quiz_session import QuizSession


async def create(
    user_id: int,
    quiz_type: str,
    total_questions: int = 10
) -> QuizSession:
    """
    Создать новую сессию квиза
    
    Args:
        user_id: Telegram ID пользователя
        quiz_type: Тип квиза (relationships, money, confidence, fears)
        total_questions: Общее количество вопросов
        
    Returns:
        Созданная сессия QuizSession
    """
    async with db.begin() as session:
        quiz_session = QuizSession(
            user_id=user_id,
            quiz_type=quiz_type,
            current_question=1,
            total_questions=total_questions,
            answers={'answers': []},
            completed=False,
            created_at=datetime.utcnow()
        )
        session.add(quiz_session)
        await session.commit()
        await session.refresh(quiz_session)
        
        return quiz_session


async def get_active(user_id: int, quiz_type: str) -> QuizSession | None:
    """
    Получить активную (незавершённую) сессию квиза
    
    Args:
        user_id: Telegram ID пользователя
        quiz_type: Тип квиза
        
    Returns:
        QuizSession или None, если активной сессии нет
    """
    async with db.begin() as session:
        result = await session.scalar(
            select(QuizSession)
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.quiz_type == quiz_type,
                    QuizSession.completed == False
                )
            )
            .order_by(QuizSession.created_at.desc())
        )
        return result


async def get_by_id(session_id: int) -> QuizSession | None:
    """Получить сессию по ID"""
    async with db.begin() as session:
        result = await session.scalar(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        return result


async def add_answer(
    session_id: int,
    question_num: int,
    question_text: str,
    answer: str
) -> None:
    """
    Добавить ответ на вопрос
    
    Args:
        session_id: ID сессии квиза
        question_num: Номер вопроса
        question_text: Текст вопроса
        answer: Ответ пользователя
    """
    async with db.begin() as session:
        quiz_session = await session.scalar(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        
        if not quiz_session:
            raise ValueError(f"Quiz session {session_id} not found")
        
        # Добавляем новый ответ
        answers = quiz_session.answers.get('answers', [])
        answers.append({
            'question_num': question_num,
            'question_text': question_text,
            'answer': answer,
            'answered_at': datetime.utcnow().isoformat()
        })
        
        # Обновляем сессию
        quiz_session.answers = {'answers': answers}
        quiz_session.current_question = question_num + 1
        quiz_session.updated_at = datetime.utcnow()
        
        await session.commit()


async def complete(
    session_id: int,
    insights: dict
) -> None:
    """
    Завершить квиз и сохранить инсайты
    
    Args:
        session_id: ID сессии квиза
        insights: Словарь с финальными инсайтами
    """
    async with db.begin() as session:
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(
                completed=True,
                insights=insights,
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()


async def get_completed(
    user_id: int,
    quiz_type: str = None,
    limit: int = 10
) -> List[QuizSession]:
    """
    Получить завершённые квизы пользователя
    
    Args:
        user_id: Telegram ID пользователя
        quiz_type: Тип квиза (если None, получает все типы)
        limit: Максимальное количество квизов
        
    Returns:
        Список QuizSession, отсортированный по дате (новые первые)
    """
    async with db.begin() as session:
        query = (
            select(QuizSession)
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.completed == True
                )
            )
            .order_by(QuizSession.completed_at.desc())
            .limit(limit)
        )
        
        if quiz_type:
            query = query.where(QuizSession.quiz_type == quiz_type)
        
        result = await session.execute(query)
        return list(result.scalars().all())


async def get_all_for_user(
    user_id: int,
    include_incomplete: bool = False
) -> List[QuizSession]:
    """
    Получить все квизы пользователя
    
    Args:
        user_id: Telegram ID пользователя
        include_incomplete: Включать ли незавершённые квизы
        
    Returns:
        Список QuizSession
    """
    async with db.begin() as session:
        query = select(QuizSession).where(QuizSession.user_id == user_id)
        
        if not include_incomplete:
            query = query.where(QuizSession.completed == True)
        
        query = query.order_by(QuizSession.created_at.desc())
        
        result = await session.execute(query)
        return list(result.scalars().all())


async def cancel(session_id: int) -> None:
    """
    Отменить (удалить) незавершённую сессию квиза
    
    Args:
        session_id: ID сессии квиза
    """
    async with db.begin() as session:
        quiz_session = await session.scalar(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        
        if quiz_session and not quiz_session.completed:
            await session.delete(quiz_session)
            await session.commit()


async def update_extra_metadata(
    session_id: int,
    extra_metadata: dict
) -> None:
    """
    Обновить метаданные сессии
    
    Args:
        session_id: ID сессии квиза
        extra_metadata: Словарь с метаданными
    """
    async with db.begin() as session:
        await session.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(
                extra_metadata=extra_metadata,
                updated_at=datetime.utcnow()
            )
        )
        await session.commit()

