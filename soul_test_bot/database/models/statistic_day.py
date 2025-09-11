from datetime import datetime
from sqlalchemy import DATE
from . import Base
from sqlalchemy.orm import Mapped, mapped_column


class Statistic_day(Base):
    __tablename__ = 'statistic_day'

    date: Mapped[datetime] = mapped_column(DATE, primary_key=True)

    new_users: Mapped[int] = mapped_column(default=0)
    return_users: Mapped[int] = mapped_column(default=0)
    block_users: Mapped[int] = mapped_column(default=0)

    refs: Mapped[int] = mapped_column(default=0)
    ads: Mapped[int] = mapped_column(default=0)
    sarafan: Mapped[int] = mapped_column(default=0)

    earn: Mapped[int] = mapped_column(default=0)
    good_requests: Mapped[int] = mapped_column(default=0)
    bad_requests: Mapped[int] = mapped_column(default=0)
    events: Mapped[int] = mapped_column(default=0)

    assistant: Mapped[int] = mapped_column(default=0)
    helper: Mapped[int] = mapped_column(default=0)
    sleeper: Mapped[int] = mapped_column(default=0)


