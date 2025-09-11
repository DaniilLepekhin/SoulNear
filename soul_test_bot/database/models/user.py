from sqlalchemy import VARCHAR
from . import Base
from .base import bigint
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[bigint] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(VARCHAR(length=64))
    username: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    ref: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)

    helper_thread_id: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    assistant_thread_id: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    sleeper_thread_id: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)

    reg_date: Mapped[datetime] = mapped_column(default=datetime.now())
    active_date: Mapped[datetime] = mapped_column(default=datetime.now())

    sub_date: Mapped[datetime] = mapped_column()
    block_date: Mapped[datetime] = mapped_column(nullable=True)

    helper_requests: Mapped[int] = mapped_column(default=10)
    assistant_requests: Mapped[int] = mapped_column(default=12)
    sleeper_requests: Mapped[int] = mapped_column(default=3)

    real_name: Mapped[str] = mapped_column(VARCHAR(length=32), nullable=True)
    age: Mapped[int] = mapped_column(nullable=True)
    gender: Mapped[bool] = mapped_column(nullable=True) # True - муж, False - жен
