"""Модуль различных хендлеров и вспомогательных методов."""
import traceback
from typing import Callable, Dict, List
from tinydb.table import Document
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, MessageEntity, User
from utils.logger import log
from utils.database import AdminDatabase, TagDatabase

db_tags = TagDatabase()
db_admins = AdminDatabase()


def check_permissions(user_id: int) -> bool:
    """Метод проверяющий наличие прав у пользователя.

    Args:
        `user_id (int)`: `ID` пользователя.

    Returns:
        `bool`: Имеет ли права пользователь.
    """
    log.info('method: check_permissions, called')
    return user_id in [item['id'] for item in db_admins.admins]


async def cmd_add_hashtag(message: Message, bot: AsyncTeleBot):
    """Хендлер команды добавляющей хештег в базу.

    Args:
        `message (Message)`: Объект сообщения.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, "У вас нет прав на выполнение этой команды!")
    else:
        text = message.text.replace('/add_hashtag', '')
        hashtags = text.split()
        for hashtag in hashtags:
            db_tags.tags = hashtag
            log.info('method: cmd_add_hashtag,hashtag: %s was added', hashtag)
        await bot.reply_to(message, "Хештег добавлен!")


async def cmd_add_admin(message: Message, bot: AsyncTeleBot):
    """Хендлер команды добавляющей администратора в базу.

    Args:
        `message (Message)`: Объект сообщения.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        fullname = ''
        contact = message.contact
        print(contact)
        if contact.first_name:
            fullname = fullname + contact.first_name
        if contact.last_name:
            fullname = fullname + contact.last_name
        db_admins.admins = {'user_id': contact.user_id,
                            'fullname': fullname,
                            'username': None,
                            'sign': " "}
        log.info('method: cmd_add_admin, admin with id %s was added', message.text)
    print(db_admins.admins)


async def cmd_remove_admin(message: Message, bot: AsyncTeleBot):
    """Хендлер команды удаляющей администратора из базы.

    Args:
        `message (Message)`: Объект сообщения.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        text = message.text.replace(
            '/remove_admin', '').strip().replace('@', '')
        db_admins.remove_admin(id=text)
        log.info('method: cmd_remove_admin, admin with id %s was deleted', text)


async def cmd_remove_hashtag(message: Message, bot: AsyncTeleBot):
    """Хендлер команды удаляющей хештег из базы.

    Args:
        `message (Message)`: Объект сообщения.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        hashtags = message.text.replace('/remove_hashtag', '').strip().split()
        for hashtag in hashtags:
            db_tags.remove_tag(hashtag)
            log.info('method: cmd_remove_hashtag, hashtag %s was deleted', hashtag)
        await bot.reply_to(message, "Хештег удален!")


async def cmd_add_sign(message: Message, bot: AsyncTeleBot):
    """Хендлер команды добавляющей приписку к сообщению.

    Args:
        `message (Message)`: Объект сообщения.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        text = message.text.replace('/add_sign ', '')
        if text == '/add_sign':
            await bot.reply_to(message, 'Примечание не указано!')
        else:
            for item in db_admins.admins:
                if message.from_user.id == item['id']:
                    db_admins.update(item['id'], {'sign': text})
                    log.info(
                        'method: cmd_add_sign, sign updated for %s, current sign: %s', item["id"], item["sign"])


def params_mapping(message_type: str, params: Dict) -> Dict:
    """Метод возвращающий необходимые параметры для сообщения на основе типа сообщения.

    Args:
        `message_type (str)`: Тип сообщения.
        `params (Dict)`: Исходные параметры сообщения.

    Returns:
        `Dict`: Необходимые параметры для сообщения.
    """
    _map = {
        'photo': ['caption', 'photo'],
        'video': ['caption', 'video'],
        'document': ['caption', 'document'],
        'text': ['text'],
        'animation': ['caption', 'animation']
    }
    map_list = [v for k in _map for v in _map[k]
                ]  # pylint: disable=consider-using-dict-items
    wanted = [wanted for _type in _map for wanted in _map[_type]
              if _type == message_type]  # pylint: disable=consider-using-dict-items
    unwanted = set(map_list) - set(wanted)
    for key in unwanted:
        params.pop(key, None)
    log.info('method: params_mapping, params: %s', params)
    return params


def get_send_procedure(message_type: str, bot: AsyncTeleBot) -> Callable:  # pylint: disable=unused-argument
    """Метод возвращающий процедуру отправки сообщения на основе типа сообщения.

    Args:
        `message_type (str)`: Тип сообщения.
        `bot (AsyncTeleBot)`: Объект бота.

    Returns:
        `Callable`: Метод отправки сообщения.
    """
    message_type = message_type.replace('text', 'message')
    log.info('method: get_send_procedure, status: done')
    func = eval(f'bot.send_{message_type}')  # pylint: disable=eval-used
    if (message_type == 'message'):
        return lambda *args, **kwargs: func(*args, **kwargs, disable_web_page_preview=True)
    return func


def string_builder(message: Document, remove_meta=True, add_sign=True) -> str:
    try:
        user: User = message.get('from_user')
        separator = '_'*15
        tags = ' '.join(list(message.get('tags') or []))
        user_link_html = f'<a href="tg://user?id={user.id}">{user.username}</a>'
        message_body = message.get('body')
        message_html_text = message_body.get('html_text')

        if remove_meta:
            # remove all after \n\n===== META =====
            message_html_text = message_html_text.split(
                '\n\n===== META =====')[0]

        text_html = f"{tags}"\
            f"\n\n{message_html_text}"

        if add_sign:
            text_html += "\n\nЕсли вас заинтересовало данное предложение напишите:\n"\
                f"{user_link_html}\n\n"
            if message.get('sign', None):
                text_html += f"{separator}"\
                    f"\n{message.get('sign')}"

        log.info('method: string_builder, text: %s', text_html)

        return text_html
    except Exception:
        log.error(traceback.format_exc())


def get_params_for_message(message_text: str, message: Message) -> Dict:
    """Метод возвращающий необходимые параметры для сообщения на основе типа сообщения.

    Args:
        `message_text (str)`: типа сообщения.
        `message (Message)`: Объект сообщения.

    Returns:
        `Dict`: Необходимые параметры для сообщения.
    """
    params = {
        'text': message_text,
        'caption': message_text,
        'photo': message.json.get('photo', [{}])[0].get('file_id', None),
        'video': message.json.get('video', {}).get('file_id', None),
        'document': message.json.get('document', {}).get('file_id', None),
        'animation': message.json.get('animation', {}).get('file_id', None)
    }
    log.info('method: get_params_for_message, params: %s', params)
    return params_mapping(message.content_type, params)


def escape(pattern):
    _special_chars_map = {i: '\\' + chr(i) for i in b'()[]{}?*+-=|<_>^$\\&~#'}
    """
    Escape special characters in a string.
    """
    if isinstance(pattern, str):
        return pattern.translate(_special_chars_map)
    else:
        pattern = str(pattern, 'latin1')
        return pattern.translate(_special_chars_map).encode('latin1')


def parse_entities(text: str, entities: List[Dict]) -> str:
    try:
        log.info('parse_entities entry')
        if not entities:
            return text
        entities.sort(key=lambda x: x.get('offset'))
        counter = 0
        emojis = []

        for i, c in enumerate(text):
            if ord(c) > 128512:
                emojis.append(i)
        for entity in entities:
            print('___________\n'+text)
            o = entity['offset'] + counter
            l = entity['length']
            if any(o > e for e in emojis):
                o -= len([e for e in emojis if o > e])
            elif any(o+l > e > o for e in emojis):
                l -= len([e for e in emojis if o+l > e > o])
            if entity['type'] in ('text_link', 'text_mention'):
                if not entity.get('url', None):
                    entity['url'] = f'tg://user?id={entity["user"]["id"]}'
                text = text[:o]+'['+text[o:o+l]+']' + \
                    f'({entity["url"]})'+text[o+l:]
                counter += 4 + len(entity['url'])
            elif entity['type'] == 'bold':
                text = text[:o]+'*'+text[o:o+l]+'*'+text[o+l:]
                counter += 2
            elif entity['type'] == 'italic':
                text = text[:o]+'_'+text[o:o+l]+'_'+text[o+l:]
                counter += 2
            elif entity['type'] == 'underline':
                text = text[:o]+'__'+text[o:o+l]+'__'+text[o+l:]
                counter += 4
            elif entity['type'] == 'spoiler':
                text = text[:o]+'||'+text[o:o+l]+'||'+text[o+l:]
                counter += 4
            elif entity['type'] == 'strikethrough':
                text = text[:o]+'~'+text[o:o+l]+'~'+text[o+l:]
                counter += 2
            elif entity['type'] == 'pre':
                text = text[:o]+'`'+text[o:o+l]+'`'+text[o+l:]
                counter += 2
            elif entity['type'] == 'code':
                text = text[:o]+'```'+text[o:o+l]+'```'+text[o+l:]
                counter += 6
        return text
    except Exception as e:
        log.error(traceback.format_exc())


def entity_to_dict(self: MessageEntity):
    return {"type": self.type,
            "offset": self.offset,
            "length": self.length,
            "url": self.url,
            "user": self.user.to_dict() if self.user else None,
            "language":  self.language,
            "custom_emoji_id": self.custom_emoji_id}


def calculate_offset(increment, entities: List[MessageEntity]):
    for entity in entities:
        entity.offset += increment
    log.info('CALCULATE_OFFSET RETURN: %s', entities)
    return entities
