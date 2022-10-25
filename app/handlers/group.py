"""Модуль групповых хендлеров"""
from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.database import AdminDatabase, UnmarkedMessages
from utils.database import memory as messages
from utils.helpers import (edit_message, get_html_text_of_message,
                           get_message_text_type, get_user_link_from_message,
                           make_meta_string, message_text_filter)
from utils.logger import log
from utils.premoderation.helpers import get_sender_of_message

from handlers.admin_configs import get_params_for_message, get_send_procedure

if TYPE_CHECKING:
    from bot import Bot

db_admins = AdminDatabase()
db_messages = UnmarkedMessages()


async def send_info_message(message: Message, bot: Bot):
    """Method for sending info message to group, when new message was send to moderator"""
    user_link = get_user_link_from_message(message)
    message = await bot.send_message(message.chat.id,
                                     f'Спасибо за пост, {user_link}, '
                                     'он будет опубликован после проверки администратора.')
    await asyncio.sleep(30)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.id)


def create_markup() -> InlineKeyboardButton:
    """Метод создающий разметку сообщения

    Returns:
        `InlineKeyboardButton`: Разметка сообщения
    """
    def command(action):
        return '/post_processing ' + action

    message_check_markup = InlineKeyboardMarkup()
    accept_button = InlineKeyboardButton(
        '✅ Принять', callback_data=command('accept'))
    decline_button = InlineKeyboardButton(
        '❌ Отклонить', callback_data=command('decline'))
    message_check_markup.add(accept_button, decline_button)
    return message_check_markup


async def on_message_received(message: Message, bot: Bot):
    """Хендлер срабатывающий на сообщения в чате

    Args:
        `message (Message)`: объект сообщения
        `bot (Bot)`: объект бота
    """
    sender = get_sender_of_message(message)
    if sender['chat_id'] in bot.premoderation.whitelist:
        return

    message_type = message.content_type

    name = message.from_user.username if message.from_user.username else message.from_user.full_name
    html_text = get_html_text_of_message(message)

    log.info('method: on_message_received'
             'Received message: %s from %s, %s', html_text, name, message.from_user.id)
    log.info('method: on_message_received, full recieved message: %s', message.json)

    if message_type in ('text', 'photo', 'video', 'document', 'hashtag', 'animation'):
        meta = make_meta_string(sender)

        params = get_params_for_message(html_text, message)
        params['reply_markup'] = create_markup()

        for admin in db_admins.admins:
            params['chat_id'] = admin.get('id')
            text_type = get_message_text_type(message)
            params[f'{text_type}'] = message_text_filter(
                html_text) + meta
            try:
                msg = await get_send_procedure(message_type, bot)(**params)
                msg_id = msg.message_id
                message_json = message.json
                message_json['msg_id'] = msg_id
                message_json['html_text'] = message_text_filter(
                    get_html_text_of_message(message))
                message_json['meta'] = meta
                message_json['sender'] = get_sender_of_message(message)

                messages.insert(message_json)

                # TODO: remove to fix admin moderation
                edit_message(bot, msg, message_json['html_text'])

            except Exception as ex:  # pylint: disable=broad-except
                log.error('Error sending procedure: %s, %s',
                          ex, traceback.format_exc())

                ex_msg = ("ВНИМАНИЕ! "
                          "ПРИ АВТОМАТИЧЕСКОЙ ОБРАБОТКИ ЭТОГО СООБЩЕНИЯ ПРОИЗОШЛА ОШИБКА!!!\n"
                          "ОБРАБОТАЙТЕ В РУЧНОМ РЕЖИМЕ\n\n")
                ex_suffix = "\n\nОТПРАВЬТЕ ПРАВИЛЬНЫЙ ТЕКСТ ОТВЕТОМ НА ЭТО СООБЩЕНИЕ"

                if params.get('text', None):
                    params['text'] = ex_msg +\
                        (message.text if message.text else message.caption) +\
                        ex_suffix
                elif params.get('caption', None):
                    params['caption'] = ex_msg +\
                        (message.text if message.text else message.caption) +\
                        ex_suffix

                await get_send_procedure(message_type, bot)(**params)

            log.info('method: on_message_received, '
                     'called for admin_id %s with params: %s',
                     params["chat_id"], params)

    await bot.delete_message(message.chat.id, message.id)
    log.info('method: on_message_received, message deleted')
    await send_info_message(message, bot)
    log.info('method: on_message_received, info message sended')
    # сохраняем сообщение
    # удаляем сообщение
    # отправляем админам
