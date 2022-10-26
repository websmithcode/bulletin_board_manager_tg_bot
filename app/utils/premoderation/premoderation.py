"""Premoderation module."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from telebot.types import Message

from utils.database import BannedSenders

from .handlers import (EmojiTool, WhiteList, Length,
                       BannedUsersValidationHandler)

if TYPE_CHECKING:
    from bot import Bot


class Premoderation:  # pylint: disable=too-few-public-methods
    """Premoderation class."""

    def __init__(self, bot: Bot, logger: logging.Logger) -> None:
        """Initialize class."""

        self.bot = bot
        self.config = bot.config
        self.log = logger
        self.emoji_tool = EmojiTool(self)
        self.length_tool = Length(self)

        def is_banned_callback(sender):
            return not BannedSenders().has(sender.get('chat_id'))

        self.banned_validator = BannedUsersValidationHandler(
            self, is_banned_callback)

        self.whitelist = WhiteList(self)

        self._limits = {
            'caption': 1024,
            'text': 4096,
            'emoji': None
        }
        self.validators = [
            self.whitelist.validate,
            self.banned_validator.validate,
        ]

    def process_message(self, message: Message) -> bool:
        """Process message."""
        for validator in self.validators:
            res = validator(message)
            self.log.info("Validator result: %s", res)
            if res.get('status') is not Premoderation.Status.VALID:
                self.log.info("Message is declined on premoderation: %s", res)
                return res

        self.log.info("Message is validated on premoderation: %s", res)
        return self.Status.valid()

    def get_limit(self, key: str, fallback=None) -> int:
        """Get limit value"""
        return self._limits.get(key, fallback)

    def set_limit(self, key: str, value: int) -> None:
        """Set limit value"""
        self._limits[key] = value

    def limit_caption(self, val: int = 1024) -> None:
        """Set caption limit."""
        self.validators.append(self.length_tool.caption_validate)
        self.set_limit('caption', val)

    def limit_text(self, val: int = 4096) -> None:
        """Set text limit."""
        self.validators.append(self.length_tool.text_validate)
        self.set_limit('text',  val)

    def limit_emoji(self, val: int = 5) -> None:
        """Set emoji limit."""
        self.validators.append(self.emoji_tool.validate)
        self.set_limit('emoji', val)

    class Status(Enum):
        """Premoderation status enum."""
        DECLINE = 0
        VALID = 1
        WHITELIST = 2

        @classmethod
        def get_status(cls, status: Premoderation.Status, text: str = None,
                       validator: str | None = None) -> dict:
            """Get valid status."""
            _status = {'status': status, 'validator': validator}
            if status is cls.DECLINE:
                _status['text'] = text
            return _status

        @classmethod
        def valid(cls, validator: str | None = None) -> dict:
            """Get valid status."""
            return cls.get_status(cls.VALID, validator=validator)

        @classmethod
        def whitelist(cls, validator: str | None = None) -> dict:
            """Get whitelist status."""
            return cls.get_status(cls.WHITELIST, validator=validator)

        @classmethod
        def decline(cls, text: str, validator: str | None = None) -> dict:
            """Get decline status."""
            return cls.get_status(cls.DECLINE, text, validator=validator)
