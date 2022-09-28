"""Модуль групповых хендлеров"""
import asyncio
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from telebot.async_telebot import AsyncTeleBot
from utils.logger import log
from utils.database import AdminDatabase, UnmarkedMessages
from handlers.admin_configs import get_params_for_message, get_send_procedure

db_admins = AdminDatabase()
db_messages = UnmarkedMessages()


async def send_info_message(message, bot: AsyncTeleBot):
    message = await bot.send_message(message.chat.id, f'Спасибо за пост, [{message.from_user.username}](tg://user?id={message.from_user.id}), '
                                                       'он будет опубликован после проверки администратора', parse_mode='Markdown')
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
    print(message.entities)
    name = message.from_user.username if message.from_user.username else message.from_user.full_name
    text = message.text if message.text else message.caption
    message_type = message.content_type
    if message.chat.type not in ('group', 'supergroup'):
        return
    log.info('method: on_message_received'
             'Received message: %s from %s, %s', text, name, message.from_user.id)
    log.debug(f'method: on_message_received, full recieved message: {message}')
    if message_type in ('text', 'photo', 'video', 'document', 'hashtag', 'animation'):
        if text:
            new_text = text + f'\n\n{name}'
            entity = MessageEntity(type='text_mention',
                                   offset=len(text)+2,
                                   length=len(name),
                                   user=message.from_user.to_dict())
        else:
            new_text = name
            entity = MessageEntity(type='text_mention',
                                   offset=0,
                                   length=len(name),
                                   user=message.from_user.to_dict())

        params = get_params_for_message(new_text, message)
        # log.debug(params)
        params['reply_markup'] = create_markup()

        if message_type == 'text':
            params['entities'] = message.entities + [entity] if message.entities else [entity]
        else:
            params['caption_entities'] = message.caption_entities + [entity] if message.caption_entities else [entity]
        
        for admin in db_admins.admins:
            params['chat_id'] = admin.get('id')
            if params.get('text', None):
                params['text'] = new_text
            elif params.get('caption', None):
                params['caption'] = new_text
            # params['entities'] = message.json.get('entities')
            # print(params['entities'])
            result = await get_send_procedure(message_type, bot)(**params)
            log.info(f'method: on_message_received, called for admin_id {params["chat_id"]} with params: {params}')

    await bot.delete_message(message.chat.id, message.id)
    log.info(f'method: on_message_received, message deleted')
    await send_info_message(message, bot)
    log.info(f'method: on_message_received, info message sended')
    # сохраняем сообщение
    # удаляем сообщение
    # отправляем админам
