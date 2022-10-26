"""Limits handlers for premoderation."""
from __future__ import annotations
from enum import Enum

from typing import TYPE_CHECKING

from telebot.types import Message

from ..helpers import get_message_text_type, get_text_of_message, get_user_link_from_message

if TYPE_CHECKING:
    from ..premoderation import Premoderation


class Length:
    """Length validation handler for premoderation."""

    def __init__(self, moder: Premoderation) -> None:
        self.moder = moder
        self.valid = lambda: self.moder.Status.valid('Length')
        self.decline = lambda text: self.moder.Status.decline(text, 'Length')

    def validate(self, message: Message, limit: int) -> bool:
        """Check message length."""
        if len(get_text_of_message(message)) <= limit:
            return self.valid()

        user_link = get_user_link_from_message(message)
        return self.decline(Length.Messages.TOO_LONG.value % (user_link, limit))

    def caption_validate(self, message: Message) -> bool:
        """Validate caption."""
        if 'caption' == get_message_text_type(message):
            return self.validate(message, self.moder.get_limit('caption'))
        return self.valid()

    def text_validate(self, message: Message) -> bool:
        """Validate text."""
        if 'text' == get_message_text_type(message):
            return self.validate(message, self.moder.get_limit('text'))
        return self.valid()

    class Messages(Enum):
        """Messages for length handler."""
        TOO_LONG = '%s, Ваше сообщение слишком длинное. Сообщение не должно превышать %s символов.'
