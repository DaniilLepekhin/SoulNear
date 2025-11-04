"""
Модель истории сообщений для ChatCompletion API

Хранит все сообщения пользователя и ассистента
для поддержания контекста в ChatCompletion API.
"""
from sqlalchemy import VARCHAR, TEXT, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .base import bigint


class ConversationHistory(Base):
    __tablename__ = 'conversation_history'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[bigint] = mapped_column(ForeignKey('users.user_id'), index=True)

    # ==========================================
    # 📝 СООБЩЕНИЕ
    # ==========================================
    # Тип ассистента: helper, sleeper, quiz_relationships, quiz_money, etc.
    assistant_type: Mapped[str] = mapped_column(VARCHAR(length=64), index=True)
    
    # Роль: system, user, assistant
    role: Mapped[str] = mapped_column(VARCHAR(length=16))
    
    # Содержимое сообщения
    content: Mapped[str] = mapped_column(TEXT)
    
    # Временная метка
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    # ==========================================
    # 📊 МЕТАДАННЫЕ
    # ==========================================
    # Метаданные (токены, модель, и т.д.)
    # Формат: {
    #   "model": "gpt-4",
    #   "tokens": 150,
    #   "finish_reason": "stop",
    #   "message_id": "msg_abc123"
    # }
    extra_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Индексы для быстрого поиска
    __table_args__ = (
        # Составной индекс для эффективного поиска истории конкретного пользователя и ассистента
        Index('idx_user_assistant_timestamp', 'user_id', 'assistant_type', 'timestamp'),
    )

