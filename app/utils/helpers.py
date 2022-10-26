""" Helpers module """
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from telebot.types import KeyboardButton, Message, ReplyKeyboardMarkup

from utils.premoderation.helpers import get_sender_of_message

if TYPE_CHECKING:
    from bot import Bot


def reply_keyboard_markup_from_list(list_of_items: list, one_time_keyboard: bool = False,
                                    resize_keyboard: bool = True):
    """Create reply keyboard markup from list"""
    return ReplyKeyboardMarkup(resize_keyboard, one_time_keyboard)\
        .add(*[KeyboardButton(button) for button in list_of_items])


def remove_meta_from_text(text: str, meta_separator="===== META ====="):
    """Remove the meta section from a text"""
    if meta_separator in text:
        return text.split(meta_separator)[0].strip()
    return text


def get_user_link_from_message(message: Message) -> str:
    """Get user link from message"""
    sender = get_sender_of_message(message)
    return get_user_link(sender)


def get_user_link(sender: dict | int, text: None | str = None) -> str:
    """Get user link"""
    text = text or sender['verbose_name']
    chat_id = sender['chat_id'] if isinstance(sender, dict) else sender
    if sender.get('is_user'):
        return f"<a href='tg://user?id={chat_id}'>{text}</a>"
    return text


def get_message_text_type(message):
    """Get message text type"""
    if message.text:
        return "text"
    return "caption"


def get_html_text_of_message(message):
    """Get html text of message"""
    text_type = get_message_text_type(message)
    if text_type:
        return getattr(message, f"html_{text_type}") or ""
    return ""


def make_meta_string(sender: dict) -> str:
    """ Make meta string with user data """
    user_link_html = f'From\n{get_user_link(sender)}'
    meta = f"\n\n{'='*5} META {'='*5}\n{user_link_html}"
    return meta


def strip_emails(text: str) -> str:
    """ Strip all emails from text """
    email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return re.sub(email_regex, "", text)


def strip_mentions(text: str) -> str:
    """Strip mentions from text"""
    return re.sub(r"@(\w+)", "", text)


def collapse_spaces(text: str) -> str:
    """Collapse spaces into one. Line breaks safe."""
    return ' '.join(list(filter(lambda s: len(s) > 0, text.split(' '))))


def collapse_breaks(text: str) -> str:
    """Collapse few breaks not more then 2"""
    return re.sub(r"\n{3,}", "\n\n", text)


def strip_plain_links(text: str) -> str:
    """Strip links from text"""
    return re.sub(r"https?://\S+", "", text, flags=re.I)


def strip_links(html_text: str) -> str:
    """Strip links from html text"""
    return re.sub(r"</?a.*?>", r"", html_text)


def strip_hashtags(text: str) -> str:
    """Strip hashtags from text"""
    return re.sub(r"#(\w+)", "", text)


def strip_unavailable_tags(html_text: str) -> str:
    """Strip html tag braces, if they name is in the list"""
    whitelist = ['b', 'i', 'u', 's', 'code',
                 'pre', 'a', 'span', 'em', 'strong', 'del']

    def replacer(match):
        tag_string = match.group(1)
        tag = tag_string.split(' ')[0].strip('/')
        if tag.lower() in whitelist:
            return f"<{tag_string}>"
        return tag

    return re.sub(r"<([^>]+)>", replacer, html_text)


def message_text_filter(html_text: str) -> str:
    """Strip links and hashtags from html text and other unnecessary stuff"""
    strippers = [
        strip_links,
        strip_plain_links,
        strip_hashtags,
        strip_emails,
        strip_mentions,
        collapse_breaks,
        collapse_spaces,
        # strip_unavailable_tags
    ]
    for stripper in strippers:
        html_text = stripper(html_text)
    return html_text.strip()


async def edit_message(bot: Bot, message: Message, new_text: str, **kwargs):
    """Edit message"""
    message_text_type = get_message_text_type(message)
    params = {
        message_text_type: new_text,
        'chat_id': message.chat.id,
        'message_id': message.id,
        **kwargs
    }
    if message_text_type == "text":
        params['disable_web_page_preview'] = True

    return await getattr(bot, f"edit_message_{message_text_type}")(**params)


class Singletone(type):
    """Abstract class for singleton pattern."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singletone, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
