""" Helpers module """
import re


def remove_meta_from_text(text: str, meta_separator="===== META ====="):
    """Remove the meta section from a text"""
    if meta_separator in text:
        return text.split(meta_separator)[0].strip()
    return text


def strip_hashtags(text: str) -> str:
    """Strip hashtags from text"""
    return re.sub(r"#(\w+)", "", text)


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
