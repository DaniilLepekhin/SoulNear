from . import Base
from .base import bigint

from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[bigint] = mapped_column(primary_key=True, unique=True)
    topic_id: Mapped[bigint] = mapped_column(nullable=False)
