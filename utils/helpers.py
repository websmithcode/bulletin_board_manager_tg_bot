""" Helpers module """


def remove_meta_from_text(text, meta_separator="===== META ====="):
    """Remove the meta section from a text"""
    return text.split(meta_separator)[0].strip()
