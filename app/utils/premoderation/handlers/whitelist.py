"""Whitelist handler for premoderation."""
import json
from telebot.types import Message

from utils.premoderation.helpers import get_sender_of_message


class WhiteList(list):
    """WhiteList handler class."""

    def __init__(self, whitelist: str | list):
        if isinstance(whitelist, str):
            whitelist = json.loads(whitelist.replace("'", '"'))
        whitelist = [str(chat_id) for chat_id in whitelist]
        super().__init__(whitelist)

    def process_message(self, message: Message) -> bool:
        """Check message sender for whitelist.

        Args:
            `message (Message)`: message

        Returns:
            `bool`: is message sender in whitelist
        """

        sender_chat_id = get_sender_of_message(message)['chat_id']
        return sender_chat_id in self
