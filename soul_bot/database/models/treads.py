# from sqlalchemy import VARCHAR
# from . import Base
# from .base import bigint
# from datetime import datetime
# from sqlalchemy.orm import Mapped, mapped_column
#
#
# class Record(Base):
#     __tablename__ = 'records'
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     user_id: Mapped[bigint] = mapped_column()
#
#     doctor_type: Mapped[str] = mapped_column(VARCHAR(length=64))
#     doctor_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)
#
#     need_hour: Mapped[int] = mapped_column(nullable=True)
#     need_date: Mapped[datetime] = mapped_column(nullable=True)
