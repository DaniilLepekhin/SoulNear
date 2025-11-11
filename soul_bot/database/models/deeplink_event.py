from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, TIMESTAMP, ForeignKey, Column

from database.models.base import Base


class DeeplinkEvent(Base):
    __tablename__ = 'deeplink_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    raw_link = Column(String(128), nullable=False)
    resolved_category = Column(String(64), nullable=True)
    quiz_session_id = Column(Integer, ForeignKey('quiz_sessions.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    quiz_started_at = Column(TIMESTAMP, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<DeeplinkEvent(id={self.id}, user_id={self.user_id}, "
            f"raw_link={self.raw_link}, resolved_category={self.resolved_category}, "
            f"quiz_session_id={self.quiz_session_id})>"
        )

