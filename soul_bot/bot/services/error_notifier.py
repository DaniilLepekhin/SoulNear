from __future__ import annotations

import asyncio
import html
import json
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Optional

from aiogram.types import (
    CallbackQuery,
    Chat,
    ErrorEvent,
    Message,
    TelegramObject,
    Update,
    User,
)

from config import ADMIN_CHAT_ID

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ErrorContext:
    scope: str
    message: str
    error_type: str
    traceback_html: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    chat_id: Optional[int] = None
    chat_title: Optional[str] = None
    update_type: Optional[str] = None
    payload_preview: Optional[str] = None
    extras: MutableMapping[str, Any] = field(default_factory=dict)


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=False)


def _truncate(value: str, limit: int = 800) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _extract_user_chat(entity: TelegramObject | None) -> tuple[Optional[User], Optional[Chat]]:
    if entity is None:
        return None, None

    if isinstance(entity, Message):
        return entity.from_user, entity.chat
    if isinstance(entity, CallbackQuery):
        return entity.from_user, entity.message.chat if entity.message else None
    if isinstance(entity, ErrorEvent):
        return _extract_user_chat(entity.update)
    if isinstance(entity, Update):
        event = entity.event
        return _extract_user_chat(event)

    from_user = getattr(entity, "from_user", None)
    chat = getattr(entity, "chat", None)
    return from_user, chat


def _resolve_update_type(entity: TelegramObject | None) -> Optional[str]:
    if entity is None:
        return None
    if isinstance(entity, Update):
        return entity.event_type
    if isinstance(entity, Message):
        return "message"
    if isinstance(entity, CallbackQuery):
        return "callback_query"
    if isinstance(entity, ErrorEvent):
        return _resolve_update_type(entity.update)
    return entity.__class__.__name__


def _extract_payload(entity: TelegramObject | None) -> Optional[str]:
    if entity is None:
        return None

    try:
        if isinstance(entity, CallbackQuery):
            data = {
                "data": entity.data,
                "message_id": entity.message.message_id if entity.message else None,
            }
        elif isinstance(entity, Message):
            data = {
                "message_id": entity.message_id,
                "text": entity.text or entity.caption,
                "content_type": entity.content_type,
            }
        elif isinstance(entity, Update):
            data = {
                "update_id": entity.update_id,
                "event_type": entity.event_type,
            }
        else:
            data = entity.model_dump(exclude_none=True)  # type: ignore[call-arg]
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return _truncate(payload, 600)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Failed to serialize payload for error notification: %s", exc)
        return None


def _build_traceback_html(error: Exception | str) -> Optional[str]:
    if isinstance(error, Exception):
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    else:
        tb = str(error)

    if not tb:
        return None

    return f"<pre><code>{_escape(_truncate(tb, 1500))}</code></pre>"


def _build_error_context(
    scope: str,
    error: Exception | str,
    *,
    event: TelegramObject | None = None,
    extras: Mapping[str, Any] | None = None,
) -> ErrorContext:
    error_message = str(error)
    error_type = type(error).__name__ if isinstance(error, Exception) else "RuntimeError"
    user, chat = _extract_user_chat(event)
    context = ErrorContext(
        scope=scope,
        message=_truncate(error_message or "<empty>"),
        error_type=error_type,
        traceback_html=_build_traceback_html(error),
        user_id=user.id if isinstance(user, User) else None,
        username=user.username if isinstance(user, User) else None,
        chat_id=chat.id if isinstance(chat, Chat) else None,
        chat_title=chat.title if getattr(chat, "title", None) else None,
        update_type=_resolve_update_type(event),
        payload_preview=_extract_payload(event),
    )

    if extras:
        context.extras.update(extras)

    return context


def _format_message(context: ErrorContext) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    parts = [
        "<b>⚠️ SoulNear Bot Error</b>",
        f"• <b>Time:</b> {timestamp} UTC",
        f"• <b>Scope:</b> {_escape(context.scope)}",
        f"• <b>Type:</b> {_escape(context.error_type)}",
        f"• <b>Message:</b> {_escape(context.message)}",
    ]

    if context.update_type:
        parts.append(f"• <b>Update:</b> {_escape(context.update_type)}")
    if context.user_id:
        username = f" (@{context.username})" if context.username else ""
        parts.append(f"• <b>User:</b> {_escape(context.user_id)}{_escape(username)}")
    if context.chat_id:
        title = f' "{context.chat_title}"' if context.chat_title else ""
        parts.append(f"• <b>Chat:</b> {_escape(context.chat_id)}{_escape(title)}")

    if context.extras:
        extras_str = _truncate(json.dumps(context.extras, ensure_ascii=False, separators=(",", ":")))
        parts.append(f"• <b>Extra:</b> <code>{_escape(extras_str)}</code>")

    if context.payload_preview:
        parts.append(f"• <b>Payload:</b> <code>{_escape(context.payload_preview)}</code>")

    body = "\n".join(parts)
    if context.traceback_html:
        body = f"{body}\n{context.traceback_html}"

    return body


async def _send_notification(message: str) -> None:
    if not ADMIN_CHAT_ID:
        logger.debug("ADMIN_CHAT_ID is not configured; skipping error notification.")
        return

    try:
        from bot.loader import bot

        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception as exc:  # pragma: no cover - best effort logging
        logger.exception("Failed to deliver error notification to admin chat: %s", exc)


async def report_exception(
    scope: str,
    error: Exception | str,
    *,
    event: TelegramObject | None = None,
    extras: Mapping[str, Any] | None = None,
) -> None:
    """
    Report exception to admin chat with detailed context.
    """
    context = _build_error_context(scope, error, event=event, extras=extras)
    message = _format_message(context)
    await _send_notification(message)


def schedule_exception_report(
    scope: str,
    error: Exception | str,
    *,
    event: TelegramObject | None = None,
    extras: Mapping[str, Any] | None = None,
) -> None:
    """
    Fire-and-forget helper for scenarios where awaiting is not possible.
    """
    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.debug("No running event loop; skipping scheduled error notification for %s", scope)
        return

    loop.create_task(report_exception(scope, error, event=event, extras=extras))


class AdminChatLogHandler(logging.Handler):
    """Logging handler that forwards error-level records to the admin chat."""

    def __init__(self, level: int = logging.ERROR) -> None:
        super().__init__(level)
        self.setLevel(level)
        self._formatter = logging.Formatter(
            "[%(asctime)s][%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.ERROR:
            return
        if record.name.startswith(__name__):
            return

        try:
            formatted_message = self._formatter.format(record)
            error: Exception | str
            if record.exc_info and record.exc_info[1]:
                error = record.exc_info[1]
            else:
                error = formatted_message

            extras = {
                "logger": record.name,
                "level": logging.getLevelName(record.levelno),
            }
            schedule_exception_report(
                f"log.{record.name}",
                error,
                extras=extras,
            )
        except Exception:  # pragma: no cover - defensive logging
            pass

