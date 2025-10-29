"""
QuizSession Model для Stage 4: Dynamic Quiz System

Хранит информацию о quiz сессиях пользователя:
- Вопросы (pre-generated или dynamic)
- Ответы пользователя
- Результаты анализа (patterns, insights, recommendations)
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from database.models.base import Base


class QuizSession(Base):
    """Quiz session model"""
    
    __tablename__ = 'quiz_sessions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    # Assistant context
    assistant_type = Column(String(64), default='helper')
    
    # Quiz metadata
    category = Column(String(64), nullable=False)  # relationships, money, confidence, fears
    status = Column(String(32), nullable=False, default='in_progress')  # in_progress, completed, cancelled
    
    # Progress tracking
    current_question_index = Column(Integer, nullable=False, default=0)
    total_questions = Column(Integer, nullable=True)
    
    # Data storage (JSONB for flexibility)
    questions = Column(JSONB, nullable=False, default=list)  # [{"id": 0, "text": "..."}]
    answers = Column(JSONB, nullable=False, default=list)    # [{"question_id": 0, "text": "..."}]
    
    # Analysis results
    patterns = Column(JSONB, nullable=True)  # Patterns extracted from quiz
    insights = Column(JSONB, nullable=True)  # High-level insights
    recommendations = Column(JSONB, nullable=True)  # Actionable recommendations
    
    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    def __repr__(self):
        return f"<QuizSession(id={self.id}, user_id={self.user_id}, category={self.category}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'assistant_type': self.assistant_type,
            'category': self.category,
            'status': self.status,
            'current_question_index': self.current_question_index,
            'total_questions': self.total_questions,
            'questions': self.questions or [],
            'answers': self.answers or [],
            'patterns': self.patterns,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage"""
        if not self.total_questions:
            return 0.0
        return (self.current_question_index / self.total_questions) * 100
    
    @property
    def is_completed(self) -> bool:
        """Check if quiz is completed"""
        return self.status == 'completed'
    
    @property
    def is_in_progress(self) -> bool:
        """Check if quiz is in progress"""
        return self.status == 'in_progress'
    
    @property
    def is_cancelled(self) -> bool:
        """Check if quiz was cancelled"""
        return self.status == 'cancelled'
