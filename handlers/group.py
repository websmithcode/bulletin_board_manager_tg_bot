"""Модуль групповых хендлеров"""
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.async_telebot import AsyncTeleBot
from utils.logger import log
from telebot import asyncio_filters
import asyncio
from utils.database import AdminDatabase, UnmarkedMessages
from handlers.admin_configs import get_params_for_message, get_send_procedure

db_admins = AdminDatabase()
db_messages = UnmarkedMessages()


async def send_info_message(message, bot: AsyncTeleBot):
    message = await bot.send_message(message.chat.id, f'Спасибо за пост, [{message.from_user.username}](tg://user?id={message.from_user.id}), '
                                                       'он будет опубликован после проверки администратора')
    await asyncio.sleep(15)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.id)


def create_markup() -> InlineKeyboardButton:
    """Метод создающий разметку сообщения

    Returns:
        `InlineKeyboardButton`: Разметка сообщения
    """
    message_check_markup = InlineKeyboardMarkup()
    accept_button = InlineKeyboardButton('Принять', callback_data='accept')
    decline_button = InlineKeyboardButton('Отклонить', callback_data='decline')
    message_check_markup.add(accept_button, decline_button)
    return message_check_markup


async def on_message_received(message: Message, bot: AsyncTeleBot):
    """Хендлер срабатывающий на сообщения в чате

    Args:
        `message (Message)`: объект сообщения
        `bot (AsyncTeleBot)`: объект бота
    """
    
    if message.from_user.is_bot:
        return 
    
    name = message.from_user.username if message.from_user.username else message.from_user.full_name
    text = message.text if message.text else message.caption
    message_type = message.content_type
    if message.chat.type not in ('group', 'supergroup'):
        return
    log.info('\nmethod: on_message_received\n'
             'Received message: %s from %s, %s', text, name, message.from_user.id)
    log.debug(message)
    if message_type in ('text', 'photo', 'video', 'document', 'hashtag', 'animation'):
        if text:
            text += f'\n\n[{name}](tg://user?id={message.from_user.id})'
        else:
            text = f'\n\n[{name}](tg://user?id={message.from_user.id})'

        params = get_params_for_message(text, message)
        # log.debug(params)
        params['reply_markup'] = create_markup()

        for admin in db_admins.admins:
            params['chat_id'] = admin.get('id')
            if params.get('text', None):
                params['text'] = text + f'\n{admin["ps"]}\n'
            elif params.get('caption', None):
                params['caption'] = text + f'\n{admin["ps"]}\n'
            log.debug(f'params: {params}')
            await get_send_procedure(message_type, bot)(**params)

    # db_messages.messages = {'message_type': message.content_type,
    #                         'uid': str(message.chat.id) + '!' + str(message.id),
    #                         'message_id': message.id,
    #                         'chat_id': message.chat.id,
    #                         'text': message.text,
    #                         'caption': message.caption,
    #                         'photo': message.json.get('photo', [{}])[0].get('file_id', None),
    #                         'video': message.json.get('video', {}).get('file_id', None),
    #                         'audio': message.audio,
    #                         'sender_id': message.from_user.id}



    await bot.delete_message(message.chat.id, message.id)
    await send_info_message(message, bot)
    # сохраняем сообщение
    # удаляем сообщение
    # отправляем админам
