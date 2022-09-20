"""Точка запуска бота
"""
import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand
from telebot.util import content_type_media
from utils.logger import log
from handlers.group import on_message_received
from handlers.private import on_hashtag_choose, send_message_to_group, on_post_processing
from handlers.admin_configs import (cmd_add_hashtag,
                                    cmd_add_admin,
                                    cmd_remove_admin,
                                    cmd_remove_hashtag,
                                    cmd_add_ps)

__TOKEN = os.environ.get('TOKEN')
bot = AsyncTeleBot(__TOKEN, parse_mode='Markdown')


def register_handlers():
    """Регистрация хендлеров бота"""
    #Админские хендлеры
    bot.register_message_handler(callback=cmd_remove_hashtag,
                                 pass_bot=True,
                                 commands=['remove_hashtag'])
    bot.register_message_handler(callback=cmd_remove_admin,
                                 pass_bot=True,
                                 commands=['remove_admin'])
    bot.register_message_handler(callback=cmd_add_admin,
                                 content_types=['contact'],
                                 pass_bot=True)
    bot.register_message_handler(callback=cmd_add_hashtag,
                                 commands=['add_hashtag'],
                                 pass_bot=True)
    bot.register_message_handler(callback=cmd_add_ps,
                                 commands=['add_ps'],
                                 pass_bot=True)

    #Базовые Хендлеры
    bot.register_message_handler(callback=on_message_received,
                                 content_types=content_type_media,
                                 pass_bot=True)
    #Обработчики запросов
    bot.register_callback_query_handler(callback=on_hashtag_choose,
                                        func=lambda call: '#' in call.data,
                                        pass_bot=True)

    bot.register_callback_query_handler(callback=send_message_to_group,
                                        func=lambda call: call.data == 'end_button',
                                        pass_bot=True)

    bot.register_callback_query_handler(callback=on_post_processing,
                                        func=lambda call: call.data in ('accept', 'decline'),
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
