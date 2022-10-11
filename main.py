import configparser
from bot import Bot

config = configparser.ConfigParser()
config.read('config.ini')
bot = Bot(config['Telegram'])


def main():
    bot.start_polling()


if __name__ == '__main__':
    main()
