from datetime import datetime

from sqlalchemy import select, update

from database.database import db
from database.models.deeplink_event import DeeplinkEvent


async def create(user_id: int, raw_link: str, resolved_category: str | None) -> int:
    async with db() as session:
        event = DeeplinkEvent(
            user_id=user_id,
            raw_link=raw_link,
            resolved_category=resolved_category,
        )
        session.add(event)
        await session.flush()
        event_id = event.id
        await session.commit()
        return event_id


async def get_last_for_user(user_id: int) -> DeeplinkEvent | None:
    async with db() as session:
        result = await session.scalar(
            select(DeeplinkEvent)
            .where(DeeplinkEvent.user_id == user_id)
            .order_by(DeeplinkEvent.created_at.desc())
        )
        return result


async def attach_quiz(event_id: int, quiz_session_id: int) -> None:
    async with db() as session:
        await session.execute(
            update(DeeplinkEvent)
            .where(DeeplinkEvent.id == event_id)
            .values(
                quiz_session_id=quiz_session_id,
                quiz_started_at=datetime.utcnow(),
            )
        )
        await session.commit()

