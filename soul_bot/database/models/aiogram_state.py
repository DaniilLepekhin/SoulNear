from typing import Dict, Any, Optional

from sqlalchemy import VARCHAR
from sqlalchemy.dialects.postgresql import JSONB

from . import Base
from sqlalchemy.orm import Mapped, mapped_column

from .base import bigint


class Aiogram_state(Base):
    __tablename__ = 'aiogram_states'

    user_id: Mapped[bigint] = mapped_column(primary_key=True)
    state: Mapped[Optional[str]] = mapped_column(VARCHAR(length=128), nullable=True)
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
