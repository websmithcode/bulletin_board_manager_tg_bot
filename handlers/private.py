"""Модуль хендлеров приватных сообщений."""
import asyncio
from enum import Enum

from telebot.async_telebot import AsyncTeleBot
from telebot.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from tinydb import Query
from utils.database import AdminDatabase, TagDatabase
from utils.database import memory as messages
from utils.logger import log

from handlers.admin_configs import (check_permissions, get_params_for_message,
                                    get_send_procedure, string_builder)
from handlers.group import create_markup

db_tags = TagDatabase()
db_admins = AdminDatabase()


def get_decline_command(action: str) -> str:
    """ Returns decline command from action """
    return '/post_processing decline ' + action


class DeclineCommands(Enum):
    """ Enum of decline commands """
    MAT = {
        'command': get_decline_command('MAT'),
        'text': 'Мат',
        'reason': 'Запрещен мат и оскорбления.',
    }
    MORE_THAN_ONCE = {
        'command': get_decline_command('MORE_THAN_ONCE'),
        'text': 'Больше 1-го раза',
        'reason': 'Запрещена реклама офферов более 1-го раза в неделю.',
    }
    LINK = {
        'command': get_decline_command('LINK'),
        'text': 'Ссылка',
        'reason': 'Запрещены любые ссылки в объявлениях, ссылка для связи с вами будет добавлена автоматически.',
    }
    PHOTO_OR_FILE = {
        'command': get_decline_command('PHOTO_OR_FILE'),
        'text': 'Фото или файлы',
        'reason': 'Запрещено прикрепление фото, видео, GIF и файлов.',
    }
    AUDIO_OR_VIDEO = {
        'command': get_decline_command('AUDIO_OR_VIDEO'),
        'text': 'Аудио или видеосообщение',
        'reason': 'Запрещена отправка аудио- и видеосообщений.',
    }
    BOT = {
        'command': get_decline_command('BOT'),
        'text': 'Бот',
        'reason': 'Запрещена любая реклама от ботов.',
    }
    ANIMATED_EMOJI = {
        'command': get_decline_command('ANIMATED_EMOJI'),
        'text': 'Анимированные emoji',
        'reason': 'Запрещены анимированные emoji в тексте объявлений.',
    }
    MORE_THAN_FIVE_EMOJI = {
        'command': get_decline_command('MORE_THAN_FIVE_EMOJI'),
        'text': 'Более 5 emoji',
        'reason': 'Запрещено использование более 5 emoji в объявлении.',
    }
    HASHTAGS = {
        'command': get_decline_command('HASHTAGS'),
        'text': 'Хэштеги',
        'reason': 'Запрещено использование #хэштегов, они будут установлены автоматически.',
    }
    OTHER = {
        'command': get_decline_command('OTHER'),
        'text': 'Другое',
        'reason': 'Отклонено по личному усмотрению администратора.',
    }
    CANCEL = {  # Cancel decline command
        'command': get_decline_command('CANCEL'),
        'text': '🚫 Отмена',
    }


def get_decline_markup() -> InlineKeyboardMarkup:
    """ Returns cecline markup with reasons of decline """

    markup = InlineKeyboardMarkup()

    for command in DeclineCommands:
        markup.add(InlineKeyboardButton(
            command.value['text'],
            callback_data=command.value['command']
        ))
    return markup


def get_hashtag_markup() -> InlineKeyboardMarkup:
    """Метод создающий разметку сообщения

    Returns:
        `InlineKeyboardMarkup`: Разметка сообщения
    """
    hashtag_markup = InlineKeyboardMarkup()
    for hashtag in db_tags.tags:
        hashtag_button = InlineKeyboardButton(f'{hashtag.get("tag")}',
                                              callback_data=f'{hashtag.get("tag")}')
        hashtag_markup.add(hashtag_button)

    hashtag_markup.add(InlineKeyboardButton('✅ Завершить выбор и отправить сообщение',
                                            callback_data='end_button'))
    hashtag_markup.add(InlineKeyboardButton('🚫 Отмена',
                                            callback_data='/post_processing reset'))
    return hashtag_markup


async def on_error_message_reply(message: Message, bot: AsyncTeleBot):
    """Хендлер, срабатывающий при ошибки парсинга/отправки сообщения.

    Args:
        message (Message): Объект сообщения.
        bot (AsyncTeleBot): Объект бота.
    """
    message_type = message.content_type
    text = message.text
    params = get_params_for_message(text, message)
    params['chat_id'] = bot.config['CHAT_ID']
    params['entities'] = message.entities
    await get_send_procedure(message_type, bot)(**params)


async def decline_handler(call: CallbackQuery, bot: AsyncTeleBot):
    """ Decline handler

    Args:
        call (CallbackQuery): CallbackQuery object.
        bot (AsyncTeleBot): Bot object.
    """
    log.info('Decline handler: %s', call.data)

    decline_action = call.data.split(' ')[2] \
        if len(call.data.split(' ')) > 2 \
        else None

    match decline_action:
        case None:
            decline_markup = get_decline_markup()
            await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                                reply_markup=decline_markup)
            return
        case 'CANCEL':
            await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                                reply_markup=create_markup())
            return
        case action:
            decline_command = DeclineCommands[action] or None
            if decline_command is None:
                return

            message_document = messages.get(Query().id == call.message.id)
            html_text = string_builder(
                message_document, remove_meta=False, add_sign=False)

            content_type = 'text' if call.message.content_type == 'text' else 'caption'

            edit_message_args = {
                'chat_id': call.message.chat.id,
                'message_id': call.message.id,
                f'{content_type}': f'{html_text}'
                '\n\n❌ОТКЛОНЕНО❌'
                '\n<b>Причина:</b>'
                f'\n{decline_command.value["reason"]}',
            }
            if call.message.content_type == 'text':
                edit_message_args['disable_web_page_preview'] = True

            edit_message = getattr(bot, f'edit_message_{content_type}')
            await edit_message(**edit_message_args)
            await send_decline_notification_to_group(decline_command.value['reason'], call, bot)


async def on_post_processing(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер принятия и отклонения новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """

    # Проверка на наличие пользователя в списке администраторов
    if not check_permissions(call.from_user.id):
        return

    action = call.data.split(' ')[1]

    message = call.message

    html_text = message.html_text if message.content_type == 'text' else message.html_caption
    admin_user = db_admins.get_admin_by_id(call.from_user.id)
    sign = admin_user.get('sign', '')

    message_body = {
        **message.json,
        'html_text': html_text,
    }

    message_data = {
        'id': call.message.id,
        'body': message_body,
        'sign': sign,
        'tags': None,
        'from_user': call.from_user
    }
    message_id = messages.insert(message_data)
    log.info('New message in db: %s', message_id)

    log.info('method: on_post_processing'
             'message: callback data from callback query id %s is \'%s\'', call.id, action)
    match action:
        case 'accept':
            await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                                reply_markup=get_hashtag_markup())
        case 'decline':
            await decline_handler(call, bot)
        case 'reset':
            await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=create_markup())

    log.info('method: on_post_processing '
             'message with chat_id %s and message_Id %s was accepted '
             '%s, %s, %s',
             call.message.chat.id, call.message.id, call.id, action, call.message)


async def on_hashtag_choose(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер выбора хештегов новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('method: on_hashtag_choose'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    msg = messages.get(Query().id == call.message.id)

    hashtag = call.data
    log.info('message: %s', msg)

    tags = set(msg.get('tags') or [])
    if hashtag not in tags:
        tags.add(hashtag)
    else:
        tags.remove(hashtag)

    tags = list(tags)

    log.info('tags: %s', str(tags))

    _ = messages.update({'tags': tags}, doc_ids=[msg.doc_id])

    log.info('update: %s', _)

    message = messages.get(Query().id == call.message.id)
    log.info('\nBEFORE STRING BUILDER: %s', message)
    html__text = string_builder(message, remove_meta=False, add_sign=False)

    if call.message.content_type == 'text':
        await bot.edit_message_text(
            text=html__text,
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=get_hashtag_markup(),
            disable_web_page_preview=True
        )

    else:
        # call.message.html_caption = call.message.html_caption or ''
        await bot.edit_message_caption(
            caption=html__text,
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=get_hashtag_markup(),
        )

    log.info('method: on_hashtag_choose'
             'caption was edited, callback data from callback query'
             ' id %s is \'%s\', current message: %s',
             call.id, call.data, call.message)


async def send_post_to_group(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер отправки поста в общую группу.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('call message from user: %s', call.from_user.username)
    message_type = call.message.content_type

    message = messages.get(Query().id == call.message.id)
    text_html = string_builder(message)

    params = get_params_for_message(text_html, call.message)
    params['chat_id'] = bot.config['CHAT_ID']

    await get_send_procedure(message_type, bot)(**params)
    await bot.edit_message_reply_markup(call.message.chat.id,
                                        message_id=call.message.message_id,
                                        reply_markup='')

    result = messages.remove(Query().id == call.message.id)
    log.info('method: send_message_to_group,removed resulted message from query, message: %s',
             result)
    log.info('method: send_message_to_group'
             'message: message with id %s '
             'message: \'%s\' is sended', call.message.id, text_html)


async def send_decline_notification_to_group(
        reason_text: str, call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер отправки поста в общую группу.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('call message from user: %s', call.from_user.username)

    message = messages.get(Query().id == call.message.id)
    sender_username = message['from_user'].username
    moderator_username = call.from_user.username

    # pylint: disable=line-too-long
    text_html = f'❗️Уважаемый, @{sender_username}. Ваш пост отклонен модератором чата. Пожалуйста, ознакомьтесь с <a href="https://t.me/biznesschatt/847154">правилами</a> группы и попробуйте еще раз. Если у вас есть вопросы, обратитесь к <a href="https://t.me/{moderator_username}">администратору</a>. Спасибо за понимание.' \
        "\n\n<b>Причина отклонения:</b>" \
        f"\n{reason_text}"

    msg = await bot.send_message(bot.config['CHAT_ID'], text_html, disable_web_page_preview=True)

    removed_message_id = messages.remove(Query().id == call.message.id)
    log.info('method: send_decline_notification_to_group,removed resulted message from query, message: %s',
             removed_message_id)
    log.info('method: send_decline_notification_to_group'
             'message: message with id %s '
             'message: \'%s\' is sended', call.message.id, text_html)

    await asyncio.sleep(30)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.id)
