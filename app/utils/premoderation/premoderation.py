"""Premoderation module."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from telebot.types import Message
from utils.premoderation.handlers.whitelist import WhiteList

if TYPE_CHECKING:
    from bot import Bot


class Premoderation:  # pylint: disable=too-few-public-methods
    """Premoderation class."""

    def __init__(self, bot: Bot):
        """Initialize class."""
        self.validators = []

        self.bot = bot
        self.config = bot.config
        self.log = logging.getLogger(__name__)

        self.whitelist = WhiteList(self.config.get('CHATS_ID_WHITELIST'))

        self._limit_caption = None
        self._limit_text = None

    def process_message(self, message: Message) -> bool:
        """Process message."""
        if self.whitelist.process_message(message):
            return {'status': Premoderation.Status.WHITELIST}

        for validator in self.validators:
            res = validator(self, message)
            if not res.get('status') is Premoderation.Status.DECLINE:
                return res
        return {'status': Premoderation.Status.VALID}

    def limit_caption(self, val: int = 1024) -> None:
        """Set caption limit."""
        self._limit_caption = val

    def limit_text(self, val: int = 4096) -> None:
        """Set text limit."""
        self._limit_text = val

    class Status(Enum):
        """Premoderation status enum."""
        DECLINE = 0
        VALID = 1
        WHITELIST = 2
