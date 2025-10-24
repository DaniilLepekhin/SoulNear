"""
Модель QuizSession для Dynamic Quiz (Stage 4)

Архитектура: HYBRID (правильная структура + MVP фичи)
- JSONB для гибкости (можем добавлять поля без миграций)
- Поддержка resume (если пользователь бросил квиз)
- Расширяемая для adaptive logic в будущем
"""
from sqlalchemy import VARCHAR, ForeignKey, TEXT
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .base import bigint


class QuizSession(Base):
    """
    Сессия прохождения квиза
    
    Статусы:
    - in_progress: квиз в процессе
    - completed: успешно завершён
    - abandoned: пользователь бросил (timeout)
    - cancelled: пользователь отменил сам
    """
    __tablename__ = 'quiz_sessions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[bigint] = mapped_column(ForeignKey('users.user_id'))
    
    # ==========================================
    # 📋 БАЗОВАЯ ИНФОРМАЦИЯ
    # ==========================================
    # Категория квиза: relationships, work, emotions, habits, personality
    category: Mapped[str] = mapped_column(VARCHAR(length=64))
    
    # Статус: in_progress, completed, abandoned, cancelled
    status: Mapped[str] = mapped_column(VARCHAR(length=32), default='in_progress')
    
    # ==========================================
    # 📊 ДАННЫЕ КВИЗА (JSONB ДЛЯ ГИБКОСТИ)
    # ==========================================
    # Формат (MVP):
    # {
    #   "questions": [
    #     {
    #       "id": "q1",
    #       "text": "Как часто вы чувствуете одиночество?",
    #       "type": "scale",  # scale, text, multiple_choice
    #       "options": ["Никогда", "Редко", "Иногда", "Часто", "Постоянно"]
    #     }
    #   ],
    #   "answers": [
    #     {
    #       "question_id": "q1",
    #       "value": "Часто",
    #       "answered_at": "2025-10-24T10:00:00"
    #     }
    #   ],
    #   "current_question_index": 3,
    #   "total_questions": 10
    # }
    #
    # Формат (V2 - adaptive, добавляется БЕЗ миграций):
    # {
    #   ... всё из MVP ...
    #   "adaptive_context": "user shows high stress levels",
    #   "branching_path": "stress_management",
    #   "confidence_scores": [0.8, 0.9, 0.7],
    #   "user_profile_snapshot": {...}  # Для анализа изменений
    # }
    data: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "questions": [],
            "answers": [],
            "current_question_index": 0,
            "total_questions": 10
        }
    )
    
    # ==========================================
    # 💡 РЕЗУЛЬТАТЫ АНАЛИЗА
    # ==========================================
    # Генерируется после завершения квиза
    # Формат:
    # {
    #   "new_patterns": [...],      # Новые паттерны
    #   "insights": [...],          # Инсайты
    #   "recommendations": [...],   # Рекомендации для пользователя
    #   "confidence": 0.85          # Уверенность в результатах
    # }
    results: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # ==========================================
    # ⏱️ ВРЕМЕННЫЕ МЕТКИ
    # ==========================================
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(nullable=True)
    
    # Для resume (если пользователь бросил)
    last_activity_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # ==========================================
    # 📈 МЕТАДАННЫЕ
    # ==========================================
    # Источник: menu, notification, auto_trigger
    source: Mapped[str] = mapped_column(VARCHAR(length=32), default='menu')
    
    # Длительность прохождения (в секундах)
    duration_seconds: Mapped[int] = mapped_column(nullable=True)


# ==========================================
# 🎯 HELPER METHODS (можно добавить позже)
# ==========================================

def get_current_question(session: QuizSession) -> dict | None:
    """Получить текущий вопрос"""
    idx = session.data.get('current_question_index', 0)
    questions = session.data.get('questions', [])
    
    if idx < len(questions):
        return questions[idx]
    return None


def get_progress(session: QuizSession) -> tuple[int, int]:
    """Получить прогресс (current, total)"""
    current = session.data.get('current_question_index', 0)
    total = session.data.get('total_questions', 10)
    return (current, total)


def is_completed(session: QuizSession) -> bool:
    """Проверить завершён ли квиз"""
    current, total = get_progress(session)
    return current >= total
