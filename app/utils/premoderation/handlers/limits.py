"""Limits handlers for premoderation."""
from __future__ import annotations

from typing import TYPE_CHECKING

from telebot.types import Message

from ..helpers import get_text_of_message, get_user_link_from_message

if TYPE_CHECKING:
    from bot import Bot


def length_validator(message: Message, limit: int, bot: Bot = None) -> bool:
    """Check message length."""
    if len(get_text_of_message(message)) <= limit:
        return {'status': bot.premoderation.Status.VALID}

    user_link = get_user_link_from_message(message)
    return {'status': bot.premoderation.Status.DECLINE, 'reason': f'{user_link}, Ваше сообщение слишком длинное'}


def caption_length_validator(bot: Bot, message: Message) -> bool:
    """Check caption length."""
    return length_validator(message, bot.premoderation.caption_limit, bot)


def text_length_validator(bot: Bot, message: Message) -> bool:
    """Check text length."""
    return length_validator(message, bot.premoderation.text_limit, bot)
