import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand
from utils.logger import log
from handlers.group import on_message_received
from handlers.private import  callback_query

__TOKEN = os.environ.get('TOKEN')
bot = AsyncTeleBot(__TOKEN, parse_mode='Markdown')


def register_handlers():
    bot.register_message_handler(callback=on_message_received, content_types=['text'], pass_bot=True)
    bot.register_callback_query_handler(callback=callback_query, func=lambda call: True, pass_bot=True)


register_handlers()


# async def set_commands():
#     await bot.set_my_commands(commands=[BotCommand()])
    

def start_polling():
    log.info("Starting polling...")
    # asyncio.run(set_commands())
    asyncio.run(bot.polling(
        non_stop=True,
        skip_pending=True
    ))


if __name__ == '__main__':
    start_polling()
