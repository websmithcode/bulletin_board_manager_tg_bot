""" Admin commands """
from __future__ import annotations

from typing import TYPE_CHECKING

from telebot.types import Message, ReplyKeyboardRemove
from utils.database import AdminDatabase, TagDatabase
from utils.helpers import reply_keyboard_markup_from_list
from utils.logger import log
from utils.states import MyStates

from handlers.admin_configs import check_permissions

if TYPE_CHECKING:
    from bot import Bot


db_admins = AdminDatabase()
db_tags = TagDatabase()

START_BUTTONS = ['Добавить теги',
                 'Удалить теги',
                 'Список тегов',
                 'Добавить подпись',
                 'Отправить пост в группу']
CANCEL_BUTTONS = ['Отмена']


def create_start_commands_markup():
    """ Create markup with commands """
    return reply_keyboard_markup_from_list(START_BUTTONS)


def create_cancel_markup():
    """ Create markup with cancel button """
    return reply_keyboard_markup_from_list(CANCEL_BUTTONS)


hideBoard = ReplyKeyboardRemove()


async def get_start_commands_markup(message: Message, bot: Bot):
    """ Get markup with commands """
    log.info('\nКоманды выведены')
    if not check_permissions(message.from_user.id):
        await bot.send_message(message, "У вас нет прав на выполнение этой команды!")
    else:
        await bot.send_message(message.chat.id,
                               'Команды выведены.', reply_markup=create_start_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_start_button_choose, message.chat.id)


async def on_start_button_choose(message: Message, bot: Bot):
    """ Start button choose """
    log.info('\nВыбор кнопки')
    user_id, chat_id = message.from_user.id, message.chat.id

    if message.text == 'Добавить теги':
        await bot.set_state(user_id, MyStates.on_hashtag_add, chat_id)
        await bot.send_message(chat_id, 'Через пробел укажите теги, которые вы хотите добавить.',
                               reply_markup=create_cancel_markup())
    if message.text == 'Добавить подпись':
        await bot.set_state(user_id, MyStates.on_sign_add, chat_id)
        await bot.send_message(chat_id, 'Напишите примечание.',
                               reply_markup=create_cancel_markup())
    if message.text == 'Удалить теги':
        await bot.set_state(user_id, MyStates.on_hashtag_delete, chat_id)
        await bot.send_message(chat_id, 'Через пробел напишите теги, которые вы хотите удалить.',
                               reply_markup=create_cancel_markup())
        await on_list_of_hashtags(message, bot)
    if message.text == 'Список тегов':
        await on_list_of_hashtags(message, bot)
        await bot.set_state(user_id, MyStates.on_start_button_choose, chat_id)
    if message.text == 'Отправить пост в группу':
        await bot.set_state(user_id, MyStates.on_send_new_post_to_group, chat_id)
        await bot.send_message(chat_id, 'Напишите текст поста.',
                               reply_markup=create_cancel_markup())
    if message.text == 'Отмена':
        await on_decline(message, bot)


async def on_decline(message: Message, bot: Bot):
    """ Cancel state handler """
    user_id, chat_id = message.from_user.id, message.chat.id
    await bot.send_message(chat_id, 'Действие отменено.',
                           reply_markup=create_start_commands_markup())
    await bot.set_state(user_id, MyStates.on_start_button_choose, chat_id)
    log.info('\nОтмена произведена')


async def on_hashtag_add(message: Message, bot: Bot):
    """ Add hashtags command handler """
    log.info('\nМомент выбора хештега')
    if message.text == 'Отмена':
        await on_decline(message, bot)
    else:
        hashtags = message.text.split()
        for hashtag in hashtags:
            # prepare hastag. If not starts with #, add it, or strip extra #
            hashtag = "#" + hashtag.replace('#', '')
            db_tags.tags = hashtag
        await bot.send_message(message.chat.id, "Хештег добавлен!",
                               reply_markup=create_start_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_start_button_choose, message.chat.id)


async def on_hashtag_delete(message: Message, bot: Bot):
    """ Delete hashtags command handler """
    log.info('\nМомент удаления хештега')
    if message.text == 'Отмена':
        await on_decline(message, bot)
    else:
        hashtags = message.text.split()
        for hashtag in hashtags:
            # prepare hastag. If not starts with #, add it, or strip extra #
            hashtag = "#" + hashtag.replace('#', '')
            db_tags.remove_tag(hashtag)
        await bot.send_message(message.chat.id, "Хештег удален!",
                               reply_markup=create_start_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_start_button_choose, message.chat.id)


async def on_list_of_hashtags(message: Message, bot: Bot):
    """ List of hashtags command handler """
    tag_list = ''
    for tag in db_tags.tags:
        tag_list = tag_list + f'{tag["tag"]}\n'
    await bot.send_message(message.chat.id, 'Вот список имеющихся тегов:\n' + tag_list)
    log.info('\nСписок хештегов выведен')


async def on_sign_add(message: Message, bot: Bot):
    """ Add sign command handler """
    log.info('\nМомент добавления новой подписи')
    if message.text == 'Отмена':
        await on_decline(message, bot)
    else:
        for item in db_admins.admins:
            if message.from_user.id == item['id']:
                db_admins.update(item['id'], {'sign': message.html_text})
        await bot.send_message(message.chat.id, 'Примечание обновлено.',
                               reply_markup=create_start_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_start_button_choose, message.chat.id)


async def on_send_new_post_to_group(message: Message, bot: Bot):
    """ Change received message and send it to group """
    log.info('method: cmd_send_post_to_group')

    # Проверка на наличие пользователя в списке администраторов
    if not check_permissions(message.from_user.id):
        return

    await bot.set_state(message.from_user.id, MyStates.on_start_button_choose, message.chat.id)

    if message.text == 'Отмена':
        await on_decline(message, bot)
        return

    await bot.copy_message(bot.config['CHAT_ID'], message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, 'Пост отправлен в группу.',
                           reply_markup=create_start_commands_markup())
