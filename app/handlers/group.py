"""Модуль групповых хендлеров"""
from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from datetime import datetime
from utils.database import AdminDatabase, CalledPublicCommands, TagDatabase
from utils.database import memory as messages
from utils.helpers import (get_html_text_of_message, get_message_text_type,
                           get_user_link_from_message, make_meta_string,
                           message_text_filter)
from utils.logger import log
from utils.premoderation.helpers import get_sender_of_message

from handlers.admin_configs import get_params_for_message, get_send_procedure

if TYPE_CHECKING:
    from bot import Bot

db_admins = AdminDatabase()


async def send_info_message(message: Message, bot: Bot, text=None, timeout=30):
    """Method for sending info message to group, when new message was send to moderator"""
    user_link = get_user_link_from_message(message)
    text = text or f'Спасибо за пост, {user_link}, ' \
        'он будет опубликован после проверки администратора.'

    message = await bot.send_message(message.chat.id, text, disable_web_page_preview=True)
    log.info('method: on_message_received, info message(%s) sended', message.id)
    await asyncio.sleep(timeout)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    log.info('method: on_message_received, info message(%s) deleted', message.id)


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


async def on_group_show_hashtags(message: Message, bot: Bot):
    """ Send hashtags to group """
    await bot.delete_message(message.chat.id, message.message_id)
    command = message.text.lower()
    history = CalledPublicCommands()

    if history.exists(command):
        last_call = history.get(command)
        if last_call['last_called'] + 60 > datetime.now().timestamp():
            return
        try:
            await bot.delete_message(
                last_call['message']['chat']['id'], last_call['message']['message_id'])
        except Exception:  # pylint: disable=broad-except
            pass

    text = "Доступные категории:\n" + \
        '\n'.join([tag.get('tag') for tag in TagDatabase().tags])

    msg = await bot.send_message(message.chat.id, text)
    sender = get_sender_of_message(message)
    history.add(command, sender=sender, message=msg.json)


async def on_message_received(message: Message, bot: Bot):
    """Хендлер срабатывающий на сообщения в чате

    Args:
        `message (Message)`: объект сообщения
        `bot (Bot)`: объект бота
    """
    log.info('method: on_message_received, full recieved message: %s', message.json)

    premoderation_result = bot.premoderation.process_message(message)
    match premoderation_result['status']:
        case bot.premoderation.Status.WHITELIST:
            return
        case bot.premoderation.Status.DECLINE:
            await bot.delete_message(message.chat.id, message.message_id)
            await send_info_message(message, bot, premoderation_result.get('text'))
            return

    name = message.from_user.username if message.from_user.username else message.from_user.full_name
    html_text = get_html_text_of_message(message)

    log.info('method: on_message_received'
             'Received message: %s from %s, %s', html_text, name, message.from_user.id)

    if message.content_type in ('text', 'photo', 'video', 'document', 'hashtag', 'animation'):
        meta = make_meta_string(get_sender_of_message(message))

        params = get_params_for_message(html_text, message)
        params['reply_markup'] = create_markup()

        for admin in db_admins.admins:
            params['chat_id'] = admin.get('id')
            text_type = get_message_text_type(message)
            params[f'{text_type}'] = message_text_filter(html_text) + meta
            try:
                msg = await get_send_procedure(message.content_type, bot)(**params)
                message_json = message.json
                message_json['msg_id'] = msg.message_id
                message_json['html_text'] = message_text_filter(
                    get_html_text_of_message(message))
                message_json['meta'] = meta
                message_json['sender'] = get_sender_of_message(message)

                messages.insert(message_json)

            except Exception as ex:  # pylint: disable=broad-except
                # log.error('method: on_message_received, error: %s', exc)
                # log.error(
                #     'method: on_message_received, traceback: %s', traceback.format_exc())
                # admin_link = bot.Strings.moder_link('администратору')
                # msg = await bot.send_message(message.chat.id,
                #                              f'Обнаружена ощибка, сообщение не было отправлено. Обратитесь к {admin_link}.')

                log.error('Error sending procedure: %s, %s',
                          ex, traceback.format_exc())

                ex_msg = ("ВНИМАНИЕ! "
                          "ПРИ АВТОМАТИЧЕСКОЙ ОБРАБОТКИ ЭТОГО СООБЩЕНИЯ ПРОИЗОШЛА ОШИБКА!!!\n"
                          "ОБРАБОТАЙТЕ В РУЧНОМ РЕЖИМЕ\n\n")

                if params.get('text', None):
                    params['text'] = ex_msg +\
                        (message.text if message.text else message.caption)
                elif params.get('caption', None):
                    params['caption'] = ex_msg +\
                        (message.text if message.text else message.caption)

                await get_send_procedure(message.content_type, bot)(**params)

            log.info('method: on_message_received, '
                     'called for admin_id %s with params: %s',
                     params["chat_id"], params)

    await bot.delete_message(message.chat.id, message.id)
    log.info('method: on_message_received, message deleted')
    await send_info_message(message, bot)
