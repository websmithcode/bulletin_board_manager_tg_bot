"""Модуль хендлеров приватных сообщений."""
import os
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot.async_telebot import AsyncTeleBot
from utils.logger import log
from utils.database import TagDatabase, AdminDatabase
from handlers.admin_configs import check_permissions, get_params_for_message, get_send_procedure, parse_and_update, parse_entities
from utils.database import memory as messages
from tinydb import Query
db_tags = TagDatabase()
db_admins = AdminDatabase()


def get_hashtag_markup() -> InlineKeyboardMarkup:
    """Метод создающий разметку сообщения

    Returns:
        `InlineKeyboardMarkup`: Разметка сообщения
    """
    hashtag_markup = InlineKeyboardMarkup()
    for hashtag in db_tags.tags:
        hashtag_button = InlineKeyboardButton(f'{hashtag.get("tag")}',
                                              callback_data=f'{hashtag.get("tag")}')
        hashtag_markup.add(hashtag_button)
    end_button = InlineKeyboardButton('Завершить выбор и отправить сообщение',
                                      callback_data='end_button')
    hashtag_markup.add(end_button)
    return hashtag_markup


async def on_post_processing(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер принятия и отклонения новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('method: on_post_processing'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)

    ps = [x['ps'] for x in db_admins.admins if x['id'] == call.message.chat.id][0]
    r = messages.insert({'id': call.message.id, 'body': call.message.json, 'ps': ps, 'tags': None})
    try:
        log.debug(f'parse and update before: {messages.get(doc_id=r)}')
        parse_and_update(messages.get(doc_id=r), **messages.get(doc_id=r))
        log.debug(f'parse and update after: {messages.get(doc_id=r)}')
    except Exception as e:
        log.error(e)
    
    log.debug(call.message.json)
    # Проверка на наличие пользователя в списке администраторов
    if not check_permissions(call.from_user.id):
        return
    # log.debug(call)
    if call.data == 'accept':
        await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id,
                                            reply_markup=get_hashtag_markup())
        log.info('method: on_post_processing'
                 f'message with chat_id{call.message.chat.id} and message_Id {call.message.id} was accepted'
                 f'{call.id}, {call.data}, {call.message}')

    elif call.data == 'decline':
        text = parse_entities(messages.get(doc_id=r)['text'], messages.get(doc_id=r)['entities'])
        if len(messages.get(doc_id=r)['entities']) == 1:
            text = re.escape('\n'.join(text.split('\n')[:-1])) + '\n'+text.split('\n')[-1]
        if call.message.content_type == 'text':
            await bot.edit_message_text(chat_id=call.from_user.id,
                                        message_id=call.message.id,
                                        text=f'{text}\n❌ОТКЛОНЕНО❌',
                                        parse_mode='MarkdownV2')
            log.info('method: on_post_processing'
                      f'message with chat_id{call.message.chat.id} and message_Id {call.message.id} was decline'
                      f'{call.id}, {call.data}, {call.message}')
        else:
            await bot.edit_message_caption(chat_id=call.from_user.id,
                                           message_id=call.message.id,
                                           caption=f'{text}\n❌ОТКЛОНЕНО❌',
                                           parse_mode='MarkdownV2')
            log.info('method: on_post_processing'
                     f'caption with chat_id{call.message.chat.id} and message_Id {call.message.id} was decline'
                     f'{call.id}, {call.data}, {call.message}')

async def on_hashtag_choose(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер выбора хештегов новых сообщений.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    log.info('method: on_hashtag_choose'
             'message: callback data from callback query id %s is \'%s\'', call.id, call.data)
    # if (call.message.text and call.message.text[0] != '#') \
    #     or (call.message.caption and call.message.caption[0] != '#'):
    #     call.data = call.data + '\n'
    r = messages.get(Query().id == call.message.id)
    
    log.debug('message: {}'.format(r))
    
    tags = r['tags']
    tags.append(call.data)
    
    log.debug('tags: {}'.format(tags))
    
    
    text = ' '.join(['\\'+tag for tag in tags])+'\n'+messages.get(doc_id=r.doc_id)['text']
    text = parse_entities(text,
                          messages.get(doc_id=r.doc_id)['entities'],
                          increment=len(' '.join(['\\'+tag for tag in tags]))+1)
    
    _ = messages.update({'tags': tags},doc_ids=[r.doc_id])
    
    log.debug('update: {}'.format(_))
    
    if call.message.content_type == 'text':
        await bot.edit_message_text(text=text,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.id,
                                    reply_markup=get_hashtag_markup(),
                                    parse_mode='MarkdownV2')

    else:
        call.message.caption = '' if not call.message.caption else call.message.caption
        await bot.edit_message_caption(caption=text,
                                       chat_id=call.message.chat.id,
                                       message_id=call.message.id,
                                       reply_markup=get_hashtag_markup(),
                                       parse_mode='MarkdownV2')
        
        log.debug('method: on_hashtag_choose'
                 'caption was edited, callback data from callback query id %s is \'%s\', current message: %s',
                  call.id, call.data, call.message)


async def send_message_to_group(call: CallbackQuery, bot: AsyncTeleBot):
    """Хендлер отправки сообщения в общую группу.

    Args:
        `call (CallbackQuery)`: Объект callback'а.
        `bot (AsyncTeleBot)`: Объект бота.
    """
    # text = call.message.text if call.message.text else call.message.caption
    log.info('call message from user: %s', call.from_user.username)
    # if text is None:
    #     text = ''
    # for m in messages.all():
    #     if m.get("body").get("entities", None):
    #         if m.get('id', None) == call.message.id:
    #             print(m)
    #             username = m.get("body")["entities"][0]["user"]["username"]
    #             user_id = m.get("body")["entities"][0]["user"]["id"]
    #             text = text.replace(f'{username}',
    #                                 f'[{username}](tg://user?id={user_id})\n')
    #     else:
    #         if m.get('id', None) == call.message.id:
    #             print(m)
    #             username = m.get("body")["caption_entities"][0]["user"]["username"]
    #             user_id = m.get("body")["caption_entities"][0]["user"]["id"]
    #             text = text.replace(f'{username}',
    #                                 f'[{username}](tg://user?id={user_id})\n')
    message_type = call.message.content_type
    text = string_builder(**messages.get(Query().id == call.message.id))

    params = get_params_for_message(text, call.message)
    params['chat_id'] = os.environ.get('CHAT_ID')
    if message_type == 'text':
        params['disable_web_page_preview'] = True

    # log.debug(F'params: {params[text]}')
    print(params)
    await get_send_procedure(message_type, bot)(**params)
    await bot.edit_message_reply_markup(call.message.chat.id,
                                        message_id=call.message.message_id,
                                        reply_markup='')

    result = messages.remove(Query().id == call.message.id)
    log.debug(f'method: send_message_to_group,removed resulted message from query, message: {result}')
    log.info('method: send_message_to_group'
             'message: message with id %s '
             'message: \'%s\' is sended', call.message.id, text)
