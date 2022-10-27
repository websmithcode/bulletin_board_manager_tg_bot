"""Модуль хендлеров приватных сообщений."""
from __future__ import annotations

import asyncio
from enum import Enum
from operator import itemgetter
from typing import TYPE_CHECKING

from telebot.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from tinydb import Query
from utils.database import AdminDatabase, BannedSenders, MessagesToPreventDeletingDB, TagDatabase
from utils.database import memory as messages
from utils.helpers import (get_user_link, edit_message,
                           get_html_text_of_message, make_meta_string,
                           strip_hashtags)
from utils.logger import log

from handlers.admin_configs import (build_html_text, check_permissions,
                                    get_params_for_message, get_send_procedure)
from handlers.group import create_markup

if TYPE_CHECKING:
    from bot import Bot

db_admins = AdminDatabase()


def get_decline_command(action: str) -> str:
    """ Returns decline command from action """
    return '/post_processing decline ' + action


async def spam_handler(call: CallbackQuery, bot: Bot):  # pylint: disable=unused-argument
    """ Spam handler

    Args:
        call (CallbackQuery): CallbackQuery object.
        bot (AsyncTeleBot): Bot object.
    """
    log.info('Spam handler: %s', call.data)
    sender = messages.get(Query().msg_id == call.message.id).get('sender')
    log.info('Spamer: %s', sender)
    BannedSenders().add(sender.get('chat_id'))


class DeclineCommands(Enum):
    """ Enum of decline commands """
    MAT = {
        'command': get_decline_command('MAT'),
        'text': 'Мат',
        'reason': 'Запрещен <b>мат</b> и оскорбления.',
    }
    MORE_THAN_ONCE = {
        'command': get_decline_command('MORE_THAN_ONCE'),
        'text': 'Больше 1-го раза',
        'reason': 'Запрещена реклама офферов <b>более 1-го раза</b> в неделю.',
        'callback': spam_handler,
    }
    SCAM = {
        'command': get_decline_command('SCAM'),
        'text': 'Скам',
        'reason': 'Запрещена реклама развода и прочего <b>скама</b>.',
    }
    LINK = {
        'command': get_decline_command('LINK'),
        'text': 'Ссылка',
        'reason': 'Запрещены <b>любые ссылки</b> в объявлениях, ссылка для связи с вами будет"\
            " добавлена автоматически.',
    }
    VEILED = {
        'command': get_decline_command('VEILED'),
        'text': 'Завуалировано',
        'reason': '<b>Непонятна суть предложения</b>. Опишите подробнее ваш оффер.'
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

    def add_button(text: str, cb_data: str) -> None:
        """ Shortcut for adding button """
        btn = InlineKeyboardButton(text, callback_data=cb_data)
        hashtag_markup.add(btn)

    for tag in TagDatabase().tags:
        add_button(tag, tag)
    add_button('✅ Завершить выбор и отправить сообщение', 'end_button')
    add_button('🚫 Отмена', '/post_processing reset')

    return hashtag_markup


def get_cancel_deleting_markup() -> InlineKeyboardMarkup:
    """ Returns cancel deleting markup """

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        '🚫 Отменить автоудаление',
        callback_data='/post_cancel_deleting'
    ))
    return markup


async def on_error_message_reply(message: Message, bot: Bot):
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


async def delete_post_in_private_handler(call: CallbackQuery, bot: Bot, timeout: int = 10):
    """Handler, which deletes post in private chat"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=get_cancel_deleting_markup())
    await asyncio.sleep(timeout)
    messages_prevent_db = MessagesToPreventDeletingDB()
    if not messages_prevent_db.has(message_id):
        messages_prevent_db.remove(message_id)
        await bot.delete_message(chat_id, message_id)
        return


async def decline_handler(call: CallbackQuery, bot: Bot):
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

            if (callback := decline_command.value.get('callback')) is not None:
                await callback(call, bot)

            message_document = messages.get(Query().msg_id == call.message.id)
            html_text = build_html_text(
                message_document, remove_meta=False, add_sign=False)

            new_text = f'{html_text}'\
                '\n\n❌ОТКЛОНЕНО❌' \
                '\n<b>Причина:</b>'\
                f'\n{decline_command.value["reason"]}'

            await edit_message(bot, call.message, new_text)

            await asyncio.gather(
                send_decline_notification_to_group(
                    decline_command.value['reason'], call, bot),
                delete_post_in_private_handler(call, bot)
            )


async def accept_handler(call: CallbackQuery, bot: Bot):
    """ Accept handler

    Args:
        call (CallbackQuery): CallbackQuery object.
        bot (AsyncTeleBot): Bot object.
    """
    log.info('Accept handler: %s', call.data)

    message_document = messages.get(Query().msg_id == call.message.id)
    html_text = build_html_text(
        message_document, remove_meta=False, add_sign=False)

    new_text = f'{html_text}'\
        '\n\n✅ОДОБРЕНО✅'

    await edit_message(bot, call.message, new_text)
    await delete_post_in_private_handler(call, bot)


async def on_post_cancel_deleting(call: CallbackQuery, bot: Bot):
    """ Cancel deleting handler

    Args:
        call (CallbackQuery): CallbackQuery object.
        bot (AsyncTeleBot): Bot object.
    """
    log.info('Cancel deleting handler: %s', call.data)

    MessagesToPreventDeletingDB().add(call.message.id)
    await bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)


async def on_post_processing(call: CallbackQuery, bot: Bot):
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
    saved_message = messages.get(Query().msg_id == message.id)

    admin_user = db_admins.get_admin_by_id(call.from_user.id)
    sign = admin_user.get('sign', '')

    message_data = {
        **saved_message,
        'sign': sign,
        'tags': None,
    }
    message_id = messages.update(
        message_data, Query().msg_id == saved_message['msg_id'])
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
            log.info('Reset message %s', message.id)
            messages.update({'tags': None}, Query().msg_id == message.id)
            meta = make_meta_string(saved_message['sender'])
            new_text = saved_message.get('html_text') + meta

            await edit_message(bot, message, new_text, reply_markup=create_markup())

    log.info('method: on_post_processing '
             'message with chat_id %s and message_Id %s was accepted '
             '%s, %s, %s',
             call.message.chat.id, call.message.id, call.id, action, call.message)


async def on_hashtag_choose(call: CallbackQuery, bot: Bot):
    """Хендлер выбора хештегов новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('method: on_hashtag_choose'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    saved_message = messages.get(Query().msg_id == call.message.id)

    if saved_message is None:
        log.error(
            'method: on_hashtag_choose - message with id %s not found in database', call.message.id)
        return

    hashtag = call.data
    log.info('message: %s', saved_message)

    tags = set(saved_message.get('tags') or [])
    if hashtag not in tags:
        tags.add(hashtag)
    else:
        tags.remove(hashtag)

    tags = list(tags)

    log.info('tags: %s', str(tags))

    _ = messages.update({'tags': tags}, doc_ids=[saved_message.doc_id])

    log.info('update: %s', _)

    message = messages.get(Query().msg_id == call.message.id)
    log.info('\nBEFORE STRING BUILDER: %s', message)

    # Remove hastags and space after hastags, before readding it
    message['html_text'] = strip_hashtags(
        get_html_text_of_message(call.message)).strip()

    html__text = build_html_text(message, remove_meta=False, add_sign=False)

    await edit_message(bot, call.message, html__text,
                       reply_markup=get_hashtag_markup())

    log.info('method: on_hashtag_choose'
             'caption was edited, callback data from callback query'
             ' id %s is \'%s\', current message: %s',
             call.id, call.data, call.message)


async def send_post_to_group(call: CallbackQuery, bot: Bot):
    """Хендлер отправки поста в общую группу.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('call message from user: %s', call.from_user.username)
    message_type = call.message.content_type

    message = messages.get(Query().msg_id == call.message.id)
    html_text = build_html_text(message)

    params = get_params_for_message(html_text, call.message)
    params['chat_id'] = bot.config['CHAT_ID']

    await get_send_procedure(message_type, bot)(**params)
    await bot.edit_message_reply_markup(call.message.chat.id,
                                        message_id=call.message.message_id,
                                        reply_markup='')
    await accept_handler(call, bot)

    result = messages.remove(Query().id == call.message.id)
    log.info('method: send_message_to_group,removed resulted message from query, message: %s',
             result)
    log.info('method: send_message_to_group'
             'message: message with id %s '
             'message: \'%s\' is sended', call.message.id, html_text)


async def send_decline_notification_to_group(
        reason_text: str, call: CallbackQuery, bot: Bot):
    """Хендлер отправки поста в общую группу.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('call message from user: %s', call.from_user.username)

    message = messages.get(Query().msg_id == call.message.id)
    user_link = get_user_link(message['sender'])

    # pylint: disable=line-too-long
    text_html = f'❗️{user_link}, Ваш пост отклонен модератором чата. Пожалуйста, ознакомьтесь с {bot.Strings.rules_link("правилами")} группы и попробуйте еще раз. Если вы хотите опубликовать объявление в таком виде - воспользуйтесь {bot.Strings.sponsored_link("платным размещением")}.' \
        "\n\n<b>Причина отклонения:</b>" \
        f"\n{reason_text}"

    msg = await bot.send_message(bot.config['CHAT_ID'], text_html, disable_web_page_preview=True)

    removed_message_id = messages.remove(Query().id == call.message.id)
    log.info('method: send_decline_notification_to_group,removed resulted message from query, message: %s',
             removed_message_id)
    log.info('method: send_decline_notification_to_group'
             'message: message with id %s '
             'message: \'%s\' is sended', call.message.id, text_html)

    await asyncio.sleep(60)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.id)
