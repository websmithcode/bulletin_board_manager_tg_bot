import os
"""Модуль групповых хендлеров"""
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.async_telebot import AsyncTeleBot
from utils.logger import log
from utils.database import AdminDatabase

db = AdminDatabase()


def create_markup():
    message_check_markup = InlineKeyboardMarkup()
    accept_button = InlineKeyboardButton('Accept', callback_data='accept')
    decline_button = InlineKeyboardButton('Decline', callback_data='decline')
    message_check_markup.add(accept_button, decline_button)
    return message_check_markup


async def on_message_received(message: Message, bot: AsyncTeleBot):
    """Хендлер срабатывающий на сообщения в чате

    Args:
        message (Message): объект сообщения
        bot (AsyncTeleBot): объект бота
    """    
    if message.chat.type not in ('group', 'supergroup'): 
        return
    log.info('Received message: %s from %s', message.text, message.sender_chat.username, message.from_user.id)
    text = message.text
    text += f'\n\n[{message.from_user.username if message.from_user.username else message.from_user.full_name}](tg://user?id={message.from_user.id})'
    await bot.delete_message(message.chat.id, message.id)
    for admin in db.admins:
        await bot.send_message(admin.get('id'), message.text, reply_markup=create_markup())
    #сохраняем сообщение
    #удаляем сообщение
    #отправляем админам



