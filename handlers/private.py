from utils.logger import log
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message


async def callback_query(call, bot: AsyncTeleBot):
    log.info('callback data from callback query id %s is \'%s\'', call.id, call.data)
    if call.data == 'accept':
        await bot.send_message(admin.get('id'), 'Выберите хештеги для поста')
        on_hashtag_choose()


def on_hashtag_choose(message: Message):
    pass
