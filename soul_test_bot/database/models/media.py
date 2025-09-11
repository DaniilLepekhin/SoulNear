from typing import Optional
from sqlalchemy import VARCHAR, TEXT
from . import Base
from sqlalchemy.orm import Mapped, mapped_column


class Media(Base):
    __tablename__ = 'medias'

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column()
    position: Mapped[int] = mapped_column()

    name: Mapped[str] = mapped_column(VARCHAR(length=64))
    text: Mapped[str] = mapped_column(TEXT(), nullable=True)

    media_type: Mapped[str] = mapped_column(VARCHAR(length=8), nullable=True)
    media_id: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(VARCHAR(length=128), nullable=True)
