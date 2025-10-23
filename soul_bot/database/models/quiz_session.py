"""
Модель сессии квиза

Хранит состояние прохождения квиза пользователем:
- Текущий вопрос
- Все ответы
- Финальные инсайты
"""
from sqlalchemy import VARCHAR, TEXT, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .base import bigint


class QuizSession(Base):
    __tablename__ = 'quiz_sessions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[bigint] = mapped_column(ForeignKey('users.user_id'), index=True)

    # ==========================================
    # 🎯 ИНФОРМАЦИЯ О КВИЗЕ
    # ==========================================
    # Тип квиза: relationships, money, confidence, fears
    quiz_type: Mapped[str] = mapped_column(VARCHAR(length=64), index=True)
    
    # Текущий номер вопроса (начинается с 1)
    current_question: Mapped[int] = mapped_column(default=1)
    
    # Общее количество вопросов в квизе
    total_questions: Mapped[int] = mapped_column(default=10)

    # ==========================================
    # 💬 ОТВЕТЫ И ВОПРОСЫ
    # ==========================================
    # Все ответы пользователя
    # Формат: [
    #   {
    #     "question_num": 1,
    #     "question_text": "Как часто вы испытываете одиночество?",
    #     "answer": "Довольно часто, особенно по вечерам",
    #     "answered_at": "2025-10-20T15:30:00"
    #   },
    #   ...
    # ]
    answers: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Инсайты из квиза (заполняется после завершения)
    # Формат: {
    #   "summary": "Краткое резюме",
    #   "patterns": ["pattern1", "pattern2"],
    #   "recommendations": ["rec1", "rec2"],
    #   "key_insights": [
    #     {
    #       "insight": "Описание инсайта",
    #       "importance": "high"
    #     }
    #   ]
    # }
    insights: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # ==========================================
    # 📊 СТАТУС И МЕТАДАННЫЕ
    # ==========================================
    # Завершён ли квиз
    completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(nullable=True)
    
    # Дополнительные метаданные
    # Формат: {
    #   "started_from": "menu",
    #   "duration_minutes": 15,
    #   "model_used": "gpt-4"
    # }
    extra_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Индексы для быстрого поиска
    __table_args__ = (
        # Составной индекс для поиска активных квизов пользователя
        Index('idx_user_quiz_completed', 'user_id', 'quiz_type', 'completed'),
    )

