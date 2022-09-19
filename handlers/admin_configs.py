from utils.database import AdminDatabase, TagDatabase
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

db_tags = TagDatabase()
db_admins = AdminDatabase()


def check_permissions(user_id: int):
    return user_id in [item['id'] for item in db_admins.admins]


async def cmd_add_hashtag(message: Message, bot: AsyncTeleBot):
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, "У вас нет прав на выполнение этой команды!")
    else:
        text = message.text.replace('/add_hashtag', '')
        hashtags = text.split()
        for hashtag in hashtags:
            db_tags.tags = hashtag


async def cmd_add_admin(message: Message, bot: AsyncTeleBot):
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        contact = message.contact
        db_admins.admins = {'id': contact.user_id, 'fullname': contact.first_name + contact.last_name, 'username': None}


async def cmd_remove_admin(message: Message, bot: AsyncTeleBot):
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        text = message.text.replace('/remove_admin', '').strip().replace('@', '')
        db_admins.remove_admin(username=text)


async def cmd_remove_hashtag(message: Message, bot: AsyncTeleBot):
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        hashtags = message.text.replace('/remove_hashtag', '').strip().split()
        for hashtag in hashtags:
            db_tags.remove_tag(hashtag)


async def cmd_add_ps(message: Message, bot: AsyncTeleBot):
    if not check_permissions(message.from_user.id):
        await bot.reply_to(message, 'У вас нет прав на выполнение этой команды')
    else:
        text = message.text.replace('/add_ps ', '')
        print(text)
        for item in db_admins.admins:
            if message.from_user.id == item['id']:
                db_admins.update(item['id'], {'ps': text})
        print(db_admins.admins)