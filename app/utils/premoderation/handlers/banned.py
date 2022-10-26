"""Banned users validation handler for premoderation."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING


from ..helpers import get_sender_of_message, get_user_link

if TYPE_CHECKING:
    from telebot.types import Message
    from ..premoderation import Premoderation


class BannedUsersValidationHandler:
    """Banned users validation handler for premoderation."""

    def __init__(self, moder: Premoderation, is_banned_callback) -> None:
        self.moder = moder
        self.valid = lambda: self.moder.Status.valid('banned')
        self.decline = lambda text: self.moder.Status.decline(text, 'banned')
        self.is_banned_callback = is_banned_callback

    def validate(self,  message: Message) -> bool:
        """Validate message."""
        sender = get_sender_of_message(message)
        user_link = get_user_link(sender)
        if self.is_banned_callback(sender):
            rules_link = self.moder.bot.Strings.rules_link('правилами')
            return self.decline(self.Messages.SPAM.value % (user_link, rules_link))
        return self.valid()

    class Messages(Enum):
        """Banned users validation handler messages."""
        SPAM = "%s, превышен лимит бесплатных сообщений в чате. Пожалуйста, не спамьте и ознакомьтесь с %s чата."
