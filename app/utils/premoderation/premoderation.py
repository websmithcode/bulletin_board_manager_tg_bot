"""Premoderation module."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from utils.premoderation.handlers.whitelist import WhiteList

if TYPE_CHECKING:
    from bot import Bot


class Premoderation:  # pylint: disable=too-few-public-methods
    """Premoderation class."""

    def __init__(self, bot: Bot):
        """Initialize class."""
        self.bot = bot
        self.config = bot.config
        self.log = logging.getLogger(__name__)

        self.whitelist = WhiteList(self.config.get('CHATS_ID_WHITELIST'))
