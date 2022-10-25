"""Premoderation module."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from telebot.types import Message
from .handlers import WhiteList, caption_length_validator, text_length_validator

if TYPE_CHECKING:
    from bot import Bot


class Premoderation:  # pylint: disable=too-few-public-methods
    """Premoderation class."""

    def __init__(self, bot: Bot, logger: logging.Logger) -> None:
        """Initialize class."""
        self.validators = []

        self.bot = bot
        self.config = bot.config
        self.log = logger

        self.whitelist = WhiteList(self.config.get('CHATS_ID_WHITELIST'))

        self._limit_caption = 1024
        self._limit_text = 4096

    def process_message(self, message: Message) -> bool:
        """Process message."""
        if self.whitelist.process_message(message):
            res = {'status': Premoderation.Status.WHITELIST}
            self.log.info("Message is whitelisted on premoderation: %s", res)
            return res

        for validator in self.validators:
            res = validator(self.bot, message)
            if res.get('status') is Premoderation.Status.DECLINE:
                self.log.info("Message is declined on premoderation: %s", res)
                return res
        res = {'status': Premoderation.Status.VALID}

        self.log.info("Message is validated on premoderation: %s", res)
        return res

    @property
    def caption_limit(self) -> int:
        """Get caption limit."""
        return self._limit_caption

    @property
    def text_limit(self) -> int:
        """Get text limit."""
        return self._limit_text

    def limit_caption(self, val: int = 1024) -> None:
        """Set caption limit."""
        self.validators.append(caption_length_validator)
        self._limit_caption = val

    def limit_text(self, val: int = 4096) -> None:
        """Set text limit."""
        self.validators.append(text_length_validator)
        self._limit_text = val

    class Status(Enum):
        """Premoderation status enum."""
        DECLINE = 0
        VALID = 1
        WHITELIST = 2
