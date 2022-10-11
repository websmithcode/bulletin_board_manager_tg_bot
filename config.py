import configparser

from bot import Bot

config = configparser.ConfigParser()
config.read('config.ini')
bot = Bot(config['Telegram'])
