"""Точка запуска бота
"""
import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand
from telebot.util import content_type_media
from utils.logger import log
from handlers.group import on_message_received
from handlers.private import  callback_query, on_hashtag_choose


__TOKEN = os.environ.get('TOKEN')
bot = AsyncTeleBot(__TOKEN, parse_mode='Markdown')


def register_handlers():
    """Регистрация хендлеров бота
    """
    bot.register_message_handler(callback=on_message_received,
                                content_types=content_type_media,
                                pass_bot=True)
    bot.register_callback_query_handler(callback=callback_query,
                                        func=lambda call: True,
                                        pass_bot=True)

register_handlers()
print(content_type_media)

# async def set_commands():
#     await bot.set_my_commands(commands=[BotCommand()])


def start_polling():
    """Метод запуска получения обновлений"""
    log.info("Starting polling...")
    # asyncio.run(set_commands())
    asyncio.run(bot.polling(
        non_stop=True,
        skip_pending=True
    ))


if __name__ == '__main__':
    start_polling()
