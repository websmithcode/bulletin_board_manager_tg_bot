"""Модуль групповых хендлеров"""
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.async_telebot import AsyncTeleBot

from utils.logger import log

from utils.database import AdminDatabase

db = AdminDatabase()


def create_markup() -> InlineKeyboardButton:
    """Метод создающий разметку сообщения

    Returns:
        InlineKeyboardButton: Разметка сообщения
    """
    message_check_markup = InlineKeyboardMarkup()
    accept_button = InlineKeyboardButton('Принять', callback_data='accept')
    decline_button = InlineKeyboardButton('Отклонить', callback_data='decline')
    message_check_markup.add(accept_button, decline_button)
    return message_check_markup


async def on_message_received(message: Message, bot: AsyncTeleBot):
    """Хендлер срабатывающий на сообщения в чате

    Args:
        message (Message): объект сообщения
        bot (AsyncTeleBot): объект бота
    """
    name = message.from_user.username if message.from_user.username else message.from_user.full_name
    text = message.text if message.text else message.caption
    message_type = message.content_type
    if message.chat.type not in ('group', 'supergroup'):
        return
    print(message.caption)
    print(message.photo)
    log.info('Received message: %s from %s, %s', text, name, message.from_user.id)
    if message_type in ('text', 'photo', 'video', 'document') and text:
        text += f'\n\n[{name}](tg://user?id={message.from_user.id})'
        params = {'reply_markup': create_markup()}

        if message_type == 'text':
            send = bot.send_message
            params['text'] = text

        elif message_type == 'photo':
            send = bot.send_photo
            params['caption'] = message.caption
            # params['caption'] = text
            # возьмет только первое изображение
            # params['photo'] = message.json.get('photo')[0].get('file_id')
            params['photo'] = message.photo
            # bot.send_photo(###, message.photo, message.caption)

        elif message_type == 'video':
            # не сработает
            send = bot.send_video
            params['caption'] = text
            params['video'] = message.video

        else:
            send = bot.send_document
            params['document'] = message.document
            params['caption'] = text

        for admin in db.admins:
            params['chat_id'] = admin.get('id')
            log.debug(send)
            await send(**params)

    await bot.delete_message(message.chat.id, message.id)
    #сохраняем сообщение
    #удаляем сообщение
    #отправляем админам
    