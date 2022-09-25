from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telebot.async_telebot import AsyncTeleBot
from utils.logger import log
from utils.database import TagDatabase, AdminDatabase
from handlers.admin_configs import check_permissions, get_params_for_message, get_send_procedure
from utils.database import memory as messages
from utils.states import MyStates

db_admins = AdminDatabase()
db_tags = TagDatabase()


def create_commands_markup():
    commands_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    add_hashtag_button = KeyboardButton('Добавить хештеги')
    delete_hashtag_button = KeyboardButton('Удалить хештеги')
    list_of_hashtags_button = KeyboardButton('Список хештегов')
    add_ps_button = KeyboardButton('Добавить подпись')
    # cancel_button = KeyboardButton('Отмена')
    commands_markup.add(add_hashtag_button,
                        delete_hashtag_button,
                        add_ps_button,
                        list_of_hashtags_button)
    return commands_markup


hideBoard = ReplyKeyboardRemove()


async def get_commands_markup(message: Message, bot: AsyncTeleBot):
    log.info('\nКоманды выведены')
    if not check_permissions(message.from_user.id):
        await bot.send_message(message, "У вас нет прав на выполнение этой команды!")
    else:
        await bot.send_message(message.chat.id,
                         text='Команды выведены', reply_markup=create_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_button_choose, message.chat.id)


async def on_button_choose(message: Message, bot: AsyncTeleBot):
    log.info('\nВыбор кнопки')
    if message.text == 'Добавить хештеги':
        await bot.set_state(message.from_user.id, MyStates.on_hashtag_add, message.chat.id)
        await bot.send_message(message.chat.id, 'Через пробел укажите хештеги, которые вы хотите добавить',
                               reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена')))
    if message.text == 'Добавить подпись':
        await bot.set_state(message.from_user.id, MyStates.on_ps_add, message.chat.id)
        await bot.send_message(message.chat.id, 'Напишите примечание',
                               reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена')))
    if message.text == 'Удалить хештеги':
        await bot.set_state(message.from_user.id, MyStates.on_hashtag_delete, message.chat.id)
        await bot.send_message(message.chat.id, 'Через пробел напишите хештеги, которые вы хотите удалить',
                               reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена')))
        await on_list_of_hashtags(message, bot)
    if message.text == 'Список хештегов':
        await on_list_of_hashtags(message, bot)
        await bot.set_state(message.from_user.id, MyStates.on_button_choose, message.chat.id)
    if message.text == 'Отмена':
        await on_decline(message, bot)


async def on_decline(message: Message, bot: AsyncTeleBot):
    log.info('\nОтмена произведена')
    """
    Cancel state
    """
    await bot.send_message(message.chat.id, 'Действие отменено', reply_markup=create_commands_markup())
    await bot.set_state(message.from_user.id, MyStates.on_button_choose, message.chat.id)


async def on_hashtag_add(message: Message, bot: AsyncTeleBot):
    log.info('\nМомент выбора хештега')
    if message.text == 'Отмена':
        await on_decline(message, bot)
    else:
        hashtags = message.text.split()
        for hashtag in hashtags:
            db_tags.tags = hashtag
        await bot.send_message(message.chat.id, "Хештег добавлен!", reply_markup=create_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_button_choose, message.chat.id)


async def on_hashtag_delete(message: Message, bot: AsyncTeleBot):
    log.info('\nМомент удаления хештега')
    if message.text == 'Отмена':
        await on_decline(message, bot)
    else:
        hashtags = message.text.split()
        for hashtag in hashtags:
            db_tags.remove_tag(hashtag)
        await bot.send_message(message.chat.id, "Хештег удален!", reply_markup=create_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_button_choose, message.chat.id)


async def on_list_of_hashtags(message: Message, bot: AsyncTeleBot):
    tag_list = ''
    for tag in db_tags.tags:
        tag_list = tag_list + f'{tag["tag"]}\n'
    await bot.send_message(message.chat.id, 'Вот список имеющихся тегов:\n' + tag_list)
    log.info('\nСписок хештегов выведен')


async def on_ps_add(message: Message, bot: AsyncTeleBot):
    log.info('\nМомент добавления новой подписи')
    if message.text == 'Отмена':
        await on_decline(message, bot)
    else:
        for item in db_admins.admins:
            if message.from_user.id == item['id']:
                db_admins.update(item['id'], {'ps': message.text})
        await bot.send_message(message.chat.id, 'Примечание обновлено', reply_markup=create_commands_markup())
        await bot.set_state(message.from_user.id, MyStates.on_button_choose, message.chat.id)





