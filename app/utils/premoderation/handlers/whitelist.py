"""Whitelist handler for premoderation."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from utils.premoderation.helpers import get_sender_of_message

if TYPE_CHECKING:
    from telebot.types import Message
    from ..premoderation import Premoderation


class WhiteList(list):
    """WhiteList handler class."""

    def __init__(self, moder: Premoderation, whitelist: str | list | None = None):
        self.moder = moder
        self.valid = lambda: self.moder.Status.valid('Whitelist')
        self.whitelist = lambda: self.moder.Status.whitelist('Whitelist')

        whitelist = whitelist or self.moder.config.get('CHATS_ID_WHITELIST')
        if isinstance(whitelist, str):
            whitelist = json.loads(whitelist.replace("'", '"'))
        whitelist = [str(chat_id) for chat_id in whitelist]
        super().__init__(whitelist)

    def is_whitelisted(self, message: Message) -> bool:
        """Check message sender for whitelist.

        Args:
            `message (Message)`: message

        Returns:
            `bool`: is message sender in whitelist
        """

        sender_chat_id = get_sender_of_message(message)['chat_id']
        return sender_chat_id in self

    def validate(self, message: Message) -> Premoderation.Status:
        """Validate message sender for whitelist."""
        if self.is_whitelisted(message):
            return self.whitelist()
        return self.valid()
