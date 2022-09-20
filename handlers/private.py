"""Модуль хендлеров приватных сообщений."""
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot.async_telebot import AsyncTeleBot
from utils.logger import log
from utils.database import TagDatabase, AdminDatabase
from handlers.admin_configs import check_permissions, get_params_for_message, get_send_procedure

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


async def on_post_processing(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер принятия и отклонения новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('\nmethod: on_post_processing\n'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    # Проверка на наличие пользователя в списке администраторов
    if not check_permissions(call.from_user.id):
        return
    # log.debug(call)
    if call.data == 'accept':
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                            reply_markup=get_hashtag_markup())

    elif call.data == 'decline':
        if call.message.content_type == 'text':
            await bot.edit_message_text(chat_id=call.from_user.id,
                                        message_id=call.message.id,
                                        text=f'{call.message.text}\n❌ОТКЛОНЕНО❌')
        else:
            await bot.edit_message_caption(chat_id=call.from_user.id,
                                           message_id=call.message.id,
                                           caption=f'{call.message.caption}\n❌ОТКЛОНЕНО❌')


async def on_hashtag_choose(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер выбора хештегов новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('\nmethod: on_hashtag_choose\n'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    if (call.message.text and call.message.text[0] != '#') \
        or (call.message.caption and call.message.caption[0] != '#'):
        call.data = call.data + '\n'

    if call.message.content_type == 'text':
        await bot.edit_message_text(text=f'{call.data} ' + call.message.text,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.id,
                                    reply_markup=get_hashtag_markup())

    else:
        await bot.edit_message_caption(caption=f'{call.data} ' + call.message.caption,
                                       chat_id=call.message.chat.id,
                                       message_id=call.message.id,
                                       reply_markup=get_hashtag_markup())


async def send_message_to_group(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер отправки сообщения в общую группу.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    text = call.message.text if call.message.text else call.message.caption
    log.info('call message from user: %s', call.from_user.username)

    text = text.replace(f'{call.from_user.username}',
                        f'[{call.from_user.username}](tg://user?id={call.from_user.id})\n')
    message_type = call.message.content_type

    params = get_params_for_message(text, call.message)
    params['chat_id'] = -642685863

    # log.debug(F'params: {params[text]}')
    await get_send_procedure(message_type, bot)(**params)
    await bot.edit_message_reply_markup(call.message.chat.id,
                                        message_id=call.message.message_id,
                                        reply_markup='')
    log.info('\nmethod: send_message_to_group\n'
             'message: message with id %s\n '
             'message: \'%s\' is sended', call.message.id, text)
