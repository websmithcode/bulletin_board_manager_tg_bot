"""Модуль хендлеров приватных сообщений."""
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from telebot.async_telebot import AsyncTeleBot
from tinydb import Query
from utils.logger import log
from utils.database import TagDatabase, AdminDatabase, memory as messages
from handlers.admin_configs import (check_permissions,
                                    get_params_for_message,
                                    get_send_procedure,
                                    parse_and_update,
                                    string_builder,
                                    calculate_offset)

db_tags = TagDatabase()
db_admins = AdminDatabase()


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
    end_button = InlineKeyboardButton('Завершить выбор и отправить сообщение',
                                      callback_data='end_button')
    hashtag_markup.add(end_button)
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
    if message_type == 'text':
        params['disable_web_page_preview'] = True
    await get_send_procedure(message_type, bot)(**params)


async def on_post_processing(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер принятия и отклонения новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """

    # Проверка на наличие пользователя в списке администраторов
    if not check_permissions(call.from_user.id):
        return

    log.info('method: on_post_processing'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    admin_user = db_admins.get_admin_by_id(call.from_user.id)
    sign = admin_user.get('sign', '')

    message = call.message
    html_text = message.html_text if message.content_type == 'text' else message.html_caption

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

    # log.info(call)
    if call.data == 'accept':
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                            reply_markup=get_hashtag_markup())
        log.info('method: on_post_processing '
                 'message with chat_id %s and message_Id %s was accepted '
                 '%s, %s, %s',
                 call.message.chat.id, call.message.id, call.id, call.data, call.message)

    elif call.data == 'decline':
        #      string builder
        text, entities = string_builder(
            messages.get(Query().id == call.message.id))
        if call.message.content_type == 'text':
            await bot.edit_message_text(chat_id=call.from_user.id,
                                        message_id=call.message.id,
                                        text=f'{text}\n❌ОТКЛОНЕНО❌',
                                        entities=entities)
            log.info('method: on_post_processing'
                     'message with chat_id %s and message_Id %s was decline'
                     '%s, %s, %s',
                     call.message.chat.id, call.message.id, call.id, call.data, call.message)
        else:
            await bot.edit_message_caption(chat_id=call.from_user.id,
                                           message_id=call.message.id,
                                           caption=f'{text}\n❌ОТКЛОНЕНО❌',
                                           entities=entities)
            log.info('method: on_post_processing'
                     'caption with chat_id %s and message_Id %s was decline'
                     '%s, %s, %s',
                     call.message.chat.id, call.message.id, call.id, call.data, call.message)


async def on_hashtag_choose(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер выбора хештегов новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('method: on_hashtag_choose'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    # if (call.message.text and call.message.text[0] != '#') \
    #     or (call.message.caption and call.message.caption[0] != '#'):
    #     call.data = call.data + '\n'
    msg = messages.get(Query().id == call.message.id)

    log.info('message: %s', msg)

    tags = msg.get('tags') or []
    tags.append(call.data)

    log.info('tags: %s', tags)

    _ = messages.update({'tags': tags}, doc_ids=[msg.doc_id])

    log.info('update: %s', _)

    if call.message.content_type == 'text':
        # TODO: recalculate offsets
        #      string_builder
        message = messages.get(Query().id == call.message.id)
        log.info(
            f'\nBEFORE STRING BUILDER: {message}')
        text, entities = string_builder(message)
        entities = calculate_offset(len(tags[-1])+1, entities)
        print("ГАВНИЩЕ: ", entities, type(entities))
        await bot.edit_message_text(text=text,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.id,
                                    reply_markup=get_hashtag_markup(),
                                    entities=entities)

    else:
        call.message.caption = '' if not call.message.caption else call.message.caption
        text, entities = string_builder(message)
        entities = calculate_offset(len(tags[-1])+1, entities)
        await bot.edit_message_caption(caption=text,
                                       chat_id=call.message.chat.id,
                                       message_id=call.message.id,
                                       reply_markup=get_hashtag_markup(),
                                       caption_entities=entities)

    log.info('method: on_hashtag_choose'
             'caption was edited, callback data from callback query'
             ' id %s is \'%s\', current message: %s',
             call.id, call.data, call.message)


async def send_message_to_group(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер отправки сообщения в общую группу.

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

    if message_type == 'text':
        params['disable_web_page_preview'] = True

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
