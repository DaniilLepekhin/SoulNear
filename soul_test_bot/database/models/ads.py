from datetime import datetime
from sqlalchemy import VARCHAR
from . import Base
from sqlalchemy.orm import Mapped, mapped_column


class Ad(Base):
    __tablename__ = 'ads'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(VARCHAR(length=64))
    link: Mapped[str] = mapped_column(VARCHAR(length=16))

    views: Mapped[int] = mapped_column(default=0)
    users: Mapped[int] = mapped_column(default=0)

    cost: Mapped[int] = mapped_column(default=0)
    earn: Mapped[int] = mapped_column(default=0)

    create_date: Mapped[datetime] = mapped_column(default=datetime.now())
