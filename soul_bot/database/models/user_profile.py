"""
Модель профиля пользователя для персонализации

Хранит:
- Настройки стиля ответов (тон, личность, длина)
- Выявленные паттерны поведения
- Инсайты из анализа
- Дополнительные предпочтения
"""
from sqlalchemy import VARCHAR, TEXT, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .base import bigint


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[bigint] = mapped_column(ForeignKey('users.user_id'), unique=True)

    # ==========================================
    # 🎨 НАСТРОЙКИ СТИЛЯ ОТВЕТОВ
    # ==========================================
    # Тон общения: formal, friendly, sarcastic, motivating
    tone_style: Mapped[str] = mapped_column(VARCHAR(length=32), default='friendly')
    
    # Личность бота: mentor, friend, coach
    personality: Mapped[str] = mapped_column(VARCHAR(length=32), default='coach')
    
    # Длина сообщений: brief, medium, detailed
    message_length: Mapped[str] = mapped_column(VARCHAR(length=32), default='brief')

    # ==========================================
    # 🧠 ПАТТЕРНЫ (MODERATE STRUCTURE)
    # ==========================================
    # Выявленные паттерны поведения с embeddings
    # Формат: {
    #   "patterns": [
    #     {
    #       "id": "uuid",
    #       "type": "behavioral|emotional|cognitive",
    #       "title": "Прокрастинация при монотонной работе",
    #       "description": "Откладывает задачи когда работа кажется скучной",
    #       "evidence": ["мне грустно дождь идёт", "опять прокрастинирую"],
    #       "embedding": [0.1, 0.2, ...],  # 1536-dim vector
    #       "frequency": "high|medium|low",
    #       "first_detected": "2025-10-20T10:00:00",
    #       "last_detected": "2025-10-24T15:30:00",
    #       "occurrences": 5,
    #       "tags": ["работа", "мотивация", "погода"],
    #       "related_patterns": ["pattern_uuid_2", "pattern_uuid_3"],
    #       "confidence": 0.85
    #     }
    #   ]
    # }
    patterns: Mapped[dict] = mapped_column(JSONB, default=lambda: {"patterns": []})
    
    # ==========================================
    # 💡 ИНСАЙТЫ (MODERATE STRUCTURE)
    # ==========================================
    # Инсайты из глубокого анализа
    # Формат: {
    #   "insights": [
    #     {
    #       "id": "uuid",
    #       "category": "personality|behavior|emotional",
    #       "title": "Склонность к самокритике",
    #       "description": "Часто винит себя за отсутствие продуктивности",
    #       "impact": "negative|neutral|positive",
    #       "recommendations": [
    #         "Напоминать о достижениях",
    #         "Фокусироваться на прогрессе"
    #       ],
    #       "derived_from": ["pattern_uuid_1", "pattern_uuid_3"],
    #       "created_at": "2025-10-24T10:00:00",
    #       "last_updated": "2025-10-24T15:00:00",
    #       "priority": "high|medium|low"
    #     }
    #   ]
    # }
    insights: Mapped[dict] = mapped_column(JSONB, default=lambda: {"insights": []})
    
    # ==========================================
    # 😊 ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ
    # ==========================================
    # Текущее эмоциональное состояние и история
    # Формат: {
    #   "current_mood": "slightly_down|neutral|good|energetic",
    #   "mood_history": [
    #     {"date": "2025-10-24", "mood": "slightly_down", "triggers": ["дождь", "работа"]},
    #     {"date": "2025-10-23", "mood": "neutral"}
    #   ],
    #   "stress_level": "low|medium|high",
    #   "energy_level": "low|medium|high"
    # }
    emotional_state: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "current_mood": "neutral",
            "mood_history": [],
            "stress_level": "medium",
            "energy_level": "medium"
        }
    )
    
    # ==========================================
    # 📊 МЕТРИКИ РАЗГОВОРОВ
    # ==========================================
    # Статистика и метрики коммуникации
    # Формат: {
    #   "total_messages": 150,
    #   "avg_session_length": 12,
    #   "most_discussed_topics": [
    #     {"topic": "работа", "count": 45},
    #     {"topic": "отношения", "count": 30}
    #   ],
    #   "question_types": {
    #     "advice_seeking": 60,
    #     "venting": 30,
    #     "clarification": 10
    #   }
    # }
    # ❌ REMOVED: conversation_metrics (unused field)
    # - Declared but never updated anywhere in codebase
    # - Migration: 004_cleanup_unused_fields.sql
    
    # ==========================================
    # 🎓 LEARNING PREFERENCES
    # ==========================================
    # Что работает/не работает для пользователя
    # Формат: {
    #   "best_response_length": "brief|medium|detailed",
    #   "preferred_communication_style": "direct_with_empathy|formal|casual",
    #   "works_well": ["конкретные шаги", "примеры из жизни"],
    #   "doesnt_work": ["общие фразы", "слишком много текста"]
    # }
    learning_preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "works_well": [],
            "doesnt_work": []
        }
    )
    
    # ==========================================
    # ⚙️ ДОПОЛНИТЕЛЬНЫЕ ПРЕДПОЧТЕНИЯ
    # ==========================================
    # Custom instructions и другие настройки
    # Формат: {
    #   "custom_instructions": "Будь более конкретным в советах",
    #   "preferred_topics": ["relationships", "personal_growth"],
    #   "avoid_topics": ["politics"]
    # }
    preferences: Mapped[dict] = mapped_column(JSONB, default={})

    # ==========================================
    # 📊 МЕТАДАННЫЕ
    # ==========================================
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Количество анализов паттернов
    pattern_analysis_count: Mapped[int] = mapped_column(default=0)
    
    # Последний анализ паттернов
    last_analysis_at: Mapped[datetime] = mapped_column(nullable=True)

