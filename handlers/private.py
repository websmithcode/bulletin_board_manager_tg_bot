from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.async_telebot import AsyncTeleBot

from utils.logger import log

from utils.database import TagDatabase, AdminDatabase

db_tags = TagDatabase()
db_admins = AdminDatabase()


def create_hashtag_markup() -> InlineKeyboardMarkup:
    """Метод создающий разметку сообщения

    Returns:
        InlineKeyboardMarkup: Разметка сообщения
    """
    hashtag_markup = InlineKeyboardMarkup()
    for hashtag in db_tags.tags:
        print(f'\'{hashtag.get("tag")}\'')
        hashtag_button = InlineKeyboardButton(f'\'{hashtag.get("tag")}\'',callback_data=f'\'{hashtag.get("tag")}\'')
        hashtag_markup.add(hashtag_button)
    return hashtag_markup


async def callback_query(call, bot: AsyncTeleBot):
    log.info('callback data from callback query id %s is \'%s\'', call.id, call.data)
    
    #Проверка на наличие пользователя в списке администраторов
    if call.from_user.id not in [item['id'] for item in db_admins]:
        return
    
    print(call)
    if call.data == 'accept':
        await bot.send_message(call.from_user.id, 'Выберите хештеги для поста', reply_markup=create_hashtag_markup())
    elif call.data == 'decline':
        await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.id, text=f'{call.message.text}\t😡ОТКЛОНЕНО😡')



def on_hashtag_choose():
    pass
