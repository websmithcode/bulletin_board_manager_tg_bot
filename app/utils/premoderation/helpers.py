"""Premoderation helpers module."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from telebot.types import Message

if TYPE_CHECKING:
    from bot import Bot


def get_sender_of_message(message: Message):
    """Get sender of message."""
    chat_id = str(message.sender_chat.id)
    is_group_or_channel = sender_is_group_or_channel(message)

    if is_group_or_channel:
        username = message.sender_chat.title.strip() or message.sender_chat.username
    else:
        username = f'{message.sender_chat.first_name} {message.sender_chat.last_name}'

    logging.info("Sender of message: %s (%s)",  username, chat_id)

    return {
        'chat_id': chat_id,
        'username': username,
        'is_group_or_channel': is_group_or_channel
    }


def sender_is_group_or_channel(message: Message):
    """Check if sender of message is group or channel."""
    return (message.from_user.is_bot) and (message.sender_chat is not None)
