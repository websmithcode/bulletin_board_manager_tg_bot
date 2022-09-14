import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand
from utils.logger import log

__TOKEN = os.environ.get('TOKEN')
bot = AsyncTeleBot(__TOKEN, parse_mode='Markdown')


def register_handlers():
    pass


register_handlers()


async def set_commands():
    await bot.set_my_commands(commands=[BotCommand()])
    

def start_polling():
    log.info("Starting polling...")
    asyncio.run(set_commands())
    asyncio.run(bot.polling(
        non_stop=True,
        skip_pending=True
    ))