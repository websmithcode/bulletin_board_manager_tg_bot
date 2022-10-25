#!/usr/bin/env python
"""Main run script"""
from utils.config import config
from bot import Bot


bot = Bot(config['Telegram'])


def main():
    """ Run bot """
    bot.start_polling()


if __name__ == '__main__':
    main()
