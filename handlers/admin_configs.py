"""Модуль различных хендлеров и вспомогательных методов."""
from typing import Callable, Dict
from tinydb.table import Document
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from utils.database import AdminDatabase, TagDatabase, memory

db_tags = TagDatabase()
db_admins = AdminDatabase()




def check_permissions(user_id: int) -> bool:
    """Метод проверяющий наличие прав у пользователя.

    Args:
        `user_id (int)`: `ID` пользователя.

    Returns:
        `bool`: Имеет ли права пользователь.
    """
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
        db_admins.admins = {'id': contact.user_id,
                            'fullname': fullname,
                            'username': None,
                            'ps': " "}
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
        text = message.text.replace('/remove_admin', '').strip().replace('@', '')
        db_admins.remove_admin(id=text)


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
        await bot.reply_to(message, "Хештег удален!")


async def cmd_add_ps(message: Message, bot: AsyncTeleBot):
    """Хендлер команды добавляющей приписку к сообщению.

    Args:
        `message (Message)`: Объект сообщения.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        text = message.text.replace('/add_ps ', '')
        if text == '/add_ps':
            await bot.reply_to(message, 'Примечание не указано!')
        else:
            for item in db_admins.admins:
                if message.from_user.id == item['id']:
                    db_admins.update(item['id'], {'ps': text})
        print(db_admins.admins)


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
    map_list = [v for k in _map for v in _map[k]] #pylint: disable=consider-using-dict-items
    wanted = [wanted for _type in _map for wanted in _map[_type] if _type == message_type] #pylint: disable=consider-using-dict-items
    unwanted = set(map_list) - set(wanted)
    for key in unwanted:
        params.pop(key, None)
    return params


def get_send_procedure(message_type: str, bot: AsyncTeleBot) -> Callable: #pylint: disable=unused-argument
    """Метод возвращающий процедуру отправки сообщения на основе типа сообщения.

    Args:
        `message_type (str)`: Тип сообщения.
        `bot (AsyncTeleBot)`: Объект бота.

    Returns:
        `Callable`: Метод отправки сообщения.
    """
    message_type = message_type.replace('text', 'message')
    return eval(f'bot.send_{message_type}') #pylint: disable=eval-used


def string_builder(**kwargs):
    text = f"{' '.join([tag for tag in kwargs.pop('tags', [])])}\n"\
    f"\n{kwargs.pop('text')}\n\n"\
    "\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"\
    'Если вас заинтересовало данное предложение напишите:\n'\
    f"[{kwargs.pop('username')}](tg://user?id={kwargs.pop('user_id')})\n\n"\
    f"{kwargs.pop('ps')}"
    
    return text



def parse_and_update(message_record: Document, **kwargs):
    body = kwargs.pop('body', None)
    if not kwargs.pop('flag', False):
        entities = body.get('entities', None) if body.get('entities', None) else body.get('caption_entities', None)
        username = entities[0].get('user').get('username')
        user_id = entities[0].get('user').get('id')
        text = body.get('text', None) if body.get('text', None) else body.get('caption')
        text = text.split('\n')[0] if len(text.split('\n')) > 1 else ''
        flag = True
    else:
        entities = kwargs.pop('entities', None)
        username = kwargs.pop('username', None)
        text = kwargs.pop('text', None)
        user_id = kwargs.pop('user_id', None)

    id = kwargs.pop('id', None)
    ps = kwargs.pop('ps', None)

    _ = memory.update({
        'id': id,
        'ps': ps,
        'tags': [],
        'entities': entities,
        'username': username,
        'text': text,
        'user_id': user_id,
        'flag': flag
        }, doc_ids=[message_record.doc_id])


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
    'video': message.json.get('video', {}).get('file_id',None),
    'document': message.json.get('document', {}).get('file_id', None),
    'animation': message.json.get('animation', {}).get('file_id', None)
    }

    return params_mapping(message.content_type, params)
