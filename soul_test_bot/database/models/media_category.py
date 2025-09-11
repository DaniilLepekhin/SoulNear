from typing import Optional

from sqlalchemy import VARCHAR, TEXT
from . import Base
from sqlalchemy.orm import Mapped, mapped_column


class Media_category(Base):
    __tablename__ = 'media_categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column(unique=True)

    name: Mapped[str] = mapped_column(VARCHAR(length=32))
    text: Mapped[str] = mapped_column(TEXT())
    category: Mapped[str] = mapped_column(VARCHAR(length=32))

    media_type: Mapped[str] = mapped_column(VARCHAR(length=8), nullable=True)
    media_id: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(VARCHAR(length=128), nullable=True)
