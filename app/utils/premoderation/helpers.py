"""Premoderation helpers module."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telebot.types import Message

if TYPE_CHECKING:
    from bot import Bot


def get_sender_of_message(message: Message):
    """Get sender of message."""
    result = {
        'is_group_or_channel': sender_is_group_or_channel(message),
        'is_user': sender_is_user(message),
    }
    if result['is_group_or_channel']:
        result['chat_id'] = str(message.sender_chat.id)
        result['verbose_name'] = message.sender_chat.title.strip()\
            or message.sender_chat.username
        result['title'] = message.sender_chat.title
    else:
        result['chat_id'] = str(message.from_user.id)
        result['verbose_name'] = f'{message.from_user.first_name} {message.from_user.last_name}'
        result['username'] = message.from_user.username
        result['first_name'] = message.from_user.first_name
        result['last_name'] = message.from_user.last_name

    logging.info("Sender of message: %s (%s)",
                 result['verbose_name'], result['chat_id'])

    return result


def sender_is_group_or_channel(message: Message):
    """Check if sender of message is group or channel."""
    return (message.from_user.is_bot) and (message.sender_chat is not None)


def sender_is_user(message: Message):
    """Check if sender of message is user."""
    return message.from_user and not message.from_user.is_bot
