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
    personality: Mapped[str] = mapped_column(VARCHAR(length=32), default='friend')
    
    # Длина сообщений: brief, medium, detailed
    message_length: Mapped[str] = mapped_column(VARCHAR(length=32), default='medium')

    # ==========================================
    # 🧠 ПАТТЕРНЫ И ИНСАЙТЫ
    # ==========================================
    # Выявленные паттерны поведения
    # Формат: [
    #   {
    #     "type": "emotional_pattern",
    #     "description": "Часто упоминает одиночество",
    #     "frequency": "high",
    #     "detected_at": "2025-10-20"
    #   },
    #   ...
    # ]
    patterns: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Инсайты из анализа
    # Формат: [
    #   {
    #     "insight": "Пользователь избегает конфликтов",
    #     "confidence": 0.8,
    #     "source": "quiz_relationships",
    #     "created_at": "2025-10-20"
    #   },
    #   ...
    # ]
    insights: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Дополнительные предпочтения и метаданные
    # Формат: {
    #   "preferred_topics": ["relationships", "personal_growth"],
    #   "avoid_topics": ["politics"],
    #   "communication_style": "direct",
    #   "custom_instructions": "Будь более конкретным в советах"
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

