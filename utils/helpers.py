""" Helpers module """


def remove_meta_from_text(text, meta_separator="===== META ====="):
    """Remove the meta section from a text"""
    return text.split(meta_separator)[0].strip()


def get_message_text_type(message):
    """Get message text type"""
    if message.text:
        return "text"
    if message.caption:
        return "caption"
    return None
