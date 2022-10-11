import configparser
import sys

from bot import Bot
from utils.database import AdminDatabase

config = configparser.ConfigParser()
config.read('config.ini')
bot = Bot(config['Telegram'])


def main():
    bot.start_polling()


if __name__ == '__main__':
    # Arg --add-admin <user_id> <username> <fullname> <sign>

    if len(sys.argv) > 4 and sys.argv[1] == '--add-admin':
        db_admins = AdminDatabase()
        db_admins.add_admin(
            sys.argv[3],
            sys.argv[4],
            sys.argv[2],
            sys.argv[5] if len(sys.argv) > 5 else ''
        )
    else:
        main()
