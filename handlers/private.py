from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot.async_telebot import AsyncTeleBot

from utils.logger import log

from utils.database import TagDatabase, AdminDatabase

from handlers.admin_configs import check_permissions

db_tags = TagDatabase()


def get_hashtag_markup() -> InlineKeyboardMarkup:
    """Метод создающий разметку сообщения

    Returns:
        InlineKeyboardMarkup: Разметка сообщения
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
    log.info('callback data from callback query id %s is \'%s\'', call.id, call.data)

    # Проверка на наличие пользователя в списке администраторов
    if not check_permissions(call.from_user.id):
        return

    # log.debug(call)
    if call.data == 'accept':
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                            reply_markup=get_hashtag_markup())
    elif call.data == 'decline':
        await bot.edit_message_text(chat_id=call.from_user.id,
                                    message_id=call.message.id,
                                    text=f'{call.message.text}\n❌ОТКЛОНЕНО❌')


async def on_hashtag_choose(call: CallbackQuery, bot: AsyncTeleBot):
    if '#' in call.data:
        log.debug(call)
        if call.message.content_type == 'text':
            await bot.edit_message_text(text=call.message.text + f'\n{call.data}',
                                        chat_id=call.message.chat.id,
                                        message_id=call.message.id,
                                        reply_markup=get_hashtag_markup())
        else:
            await bot.edit_message_caption(caption=call.message.caption + f'\n{call.data}',
                                           chat_id=call.message.chat.id,
                                           message_id=call.message.id,
                                           reply_markup=get_hashtag_markup())


async def send_message_to_group(call: CallbackQuery, bot: AsyncTeleBot):
    text = call.message.text if call.message.text else call.message.caption
    log.debug(call.message.caption)
    entities = call.message.entities if call.message.entities else call.message.caption_entities
    print(call.message)

    for entity in entities:
        log.debug(entity.type)
        if entity.type == 'text_mention':
            log.debug('Проверяю entity: {}'.format(entity))
            # log.debug(call.message.from_user)
            text = text.replace(f'\n\n{entity.user.username}', '')
            text += f'\n\n[{entity.user.username}](tg://user?id={entity.user.id})'

    message_type = call.message.content_type
    params = {}
    # bot.register_next_step_handler(message, send_message_to_group)
    if call.data == 'end_button':

        if message_type == 'text':
            send = bot.send_message
            params['text'] = text

        elif message_type == 'photo':
            send = bot.send_photo
            params['caption'] = text
            # возьмет только первое изображение
            params['photo'] = call.message.json.get('photo')[0].get('file_id')

        elif message_type == 'video':
            # не сработает
            send = bot.send_video
            params['caption'] = text
            params['video'] = call.message.video.file_id

        else:
            send = bot.send_document
            params['document'] = call.message.document
            params['caption'] = text

        params['chat_id'] = -642685863
        log.debug(send)

        await send(**params)
        await bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup='')
    pass
