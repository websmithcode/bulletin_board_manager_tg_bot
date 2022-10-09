"""Модуль групповых хендлеров"""
import asyncio
import json
import traceback
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity, User
from telebot.async_telebot import AsyncTeleBot
import advertools as adv
from utils.logger import log
from utils.database import AdminDatabase, UnmarkedMessages
from handlers.admin_configs import get_params_for_message, get_send_procedure, entity_to_dict

db_admins = AdminDatabase()
db_messages = UnmarkedMessages()


MessageEntity.to_dict = entity_to_dict


async def send_info_message(msg, bot: AsyncTeleBot):
    msg = await bot.send_message(msg.chat.id,
                                'Спасибо за пост, '
                                f'[{msg.from_user.username}](tg://user?id={msg.from_user.id}), '
                                'он будет опубликован после проверки администратора',
                                parse_mode='Markdown')
    await asyncio.sleep(15)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.id)


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

    if message.chat.type not in ('group', 'supergroup'):
        return


    name = message.from_user.username if message.from_user.username else message.from_user.full_name
    text = message.text if message.text else message.caption
    entities = (message.json.get('entities')\
                if message.json.get('entities',None)\
                else message.json.get('caption_entities')) or []
    entities = [MessageEntity.de_json(json.dumps(x)) for x in entities] or []
    message_type = message.content_type
    # print(f'ENTITIES: {entities}')
    log.info('method: on_message_received'
             'Received message: %s from %s, %s', text, name, message.from_user.id)
    log.info('method: on_message_received, full recieved message: %s',message.json)

    # if entities:
    #     entities = [x.to_dict() for x in entities]
    #     #print(f'TEXT BEFORE: {text}')
    #     text = parse_entities(text, entities)
    #     #print(f'TEXT AFTER: {text}\n TYPE: {type(text)}')


    if message_type in ('text', 'photo', 'video', 'document', 'hashtag', 'animation'):
        if text:
            new_text = text + f'\n\n{name}'
            count = adv.extract_emoji(text)['overview']['num_emoji'] # Это просто пиздец
            for emoji in adv.extract_emoji(text)['emoji_flat']:
                if len(f"{ord(emoji):X}") == 4:
                    count -= 1
            print(f'EMOTICONS COUNT:{count}')
            entity = {'type': 'text_mention',
                      'offset': len(new_text)-len(name)+count,
                      'length': len(name),
                      'url': f'tg://user?id={message.from_user.id}',
                      'user': message.from_user.to_dict()
                    }
            entity = MessageEntity.de_json(json.dumps(entity))
            print(entity.user, message.json.get('from'))
        else:
            new_text = name
            entity ={'type': 'text_mention',
                    'offset':0,
                    'length':len(name),
                    'user': message.from_user.to_dict()}
            entity = MessageEntity.de_json(json.dumps(entity))

        # new_text = parse_entities(new_text, [entity])
        params = get_params_for_message(new_text, message)
        # log.info(params)
        params['reply_markup'] = create_markup()



        for admin in db_admins.admins:
            params['chat_id'] = admin.get('id')
            if params.get('text', None):
                params['text'] = new_text
                params['entities'] = entities + [entity]
            elif params.get('caption', None):
                params['caption_entities'] = entities + [entity]
            # params['entities'] = message.json.get('entities')
            # print(params['entities'])
            try:
                await get_send_procedure(message_type, bot)(**params)
            except Exception as ex:
                log.error('Error sending procedure: %s, %s', ex, traceback.format_exc())

                ex_msg = ("ВНИМАНИЕ! "
                        "ПРИ АВТОМАТИЧЕСКОЙ ОБРАБОТКИ ЭТОГО СООБЩЕНИЯ ПРОИЗОШЛА ОШИБКА!!!\n"
                        "ОБРАБОТАЙТЕ В РУЧНОМ РЕЖИМЕ\n\n")
                ex_suffix = "\n\nОТПРАВЬТЕ ПРАВИЛЬНЫЙ ТЕКСТ ОТВЕТОМ НА ЭТО СООБЩЕНИЕ"

                if params.get('text', None):
                    params['text'] = ex_msg+\
                                    (message.text if message.text else message.caption)+\
                                    ex_suffix
                elif params.get('caption', None):
                    params['caption'] = ex_msg+\
                                        (message.text if message.text else message.caption)+\
                                        ex_suffix

                await get_send_procedure(message_type, bot)(**params)

            log.info('method: on_message_received, '
                     'called for admin_id %s with params: %s',
                     params["chat_id"],params)

    await bot.delete_message(message.chat.id, message.id)
    log.info('method: on_message_received, message deleted')
    await send_info_message(message, bot)
    log.info('method: on_message_received, info message sended')
    # сохраняем сообщение
    # удаляем сообщение
    # отправляем админам
