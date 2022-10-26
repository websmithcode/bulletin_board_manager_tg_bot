"""Emoji validation handler for premoderation."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING


from emoji import emoji_count
from ..helpers import (get_text_of_message,
                       get_user_link_from_message)

if TYPE_CHECKING:
    from telebot.types import Message
    from ..premoderation import Premoderation


class EmojiTool:
    """Emoji tool class."""

    def __init__(self, moder: Premoderation) -> None:
        self.moder = moder
        self.valid = lambda: self.moder.Status.valid('Emoji')
        self.decline = lambda text: self.moder.Status.decline(text, 'Emoji')

    def validate(self,  message: Message) -> bool:
        """Validate message."""
        limit = self.moder.get_limit('emoji')
        if limit is None:
            return self.valid()

        text = get_text_of_message(message)
        count = emoji_count(text)
        if count <= limit:
            return self.valid()

        user_link = get_user_link_from_message(message)
        return self.decline(EmojiTool.Messages.TOO_MANY_EMOJI.value % (user_link, limit))

    class Messages(Enum):
        """Emoji tool message."""
        TOO_MANY_EMOJI = ('%s, Ваше сообщение содержит слишком много эмодзи. '
                          'Используйте не более %s эмодзи в сообщении.')
