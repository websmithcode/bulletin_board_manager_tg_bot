"""Точка запуска бота"""
import os
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.util import content_type_media
from utils.logger import log
from handlers.group import on_message_received
from handlers.private import on_hashtag_choose, send_message_to_group, on_post_processing
from handlers.admin_configs import (cmd_add_hashtag,
                                    cmd_add_admin,
                                    cmd_remove_admin,
                                    cmd_remove_hashtag,
                                    cmd_add_ps)


from handlers.admin_commands import (get_commands_markup,
                                     on_button_choose,
                                     on_hashtag_add,
                                     on_ps_add,
                                     on_hashtag_delete)

from telebot.asyncio_storage import StateMemoryStorage
from telebot import asyncio_filters
from utils.states import MyStates


class Bot(AsyncTeleBot):
    def __init__(self, config, **kwargs):
        self.config = config
        super().__init__(self.config['TOKEN'], **kwargs)
        self.commands = [
            # Admin handlers
            {
                'callback': cmd_remove_hashtag,
                'commands': ['remove_hashtag']
            },
            {
                'callback': cmd_remove_admin,
                'commands': ['remove_admin']
            },
            {
                'callback': cmd_add_admin,
                'content_types': ['contact'],
            },
            {
                'callback': cmd_add_hashtag,
                'commands': ['add_hashtag'],
            },
            {
                'callback': cmd_add_ps,
                'commands': ['add_ps'],
            },
            # Admin button handlers
            {
                'callback': get_commands_markup,
                'commands': ['start'],
            },
            {
                'callback': on_button_choose,
                'state': MyStates.on_button_choose,
            },
            {
                'callback': on_hashtag_add,
                'state': MyStates.on_hashtag_add,
            },
            {
                'callback': on_hashtag_delete,
                'state': MyStates.on_hashtag_delete,
            },
            {
                'callback': on_ps_add,
                'state': MyStates.on_ps_add,
            },
            # Basic handlers
            {
                'callback': on_message_received,
                'content_types': content_type_media,
            },
            # Query handlers
            {
                'callback': on_hashtag_choose,
                'func': lambda call: '#' in call.data,
            },
            {
                'callback': send_message_to_group,
                'func': lambda call: call.data == 'end_button',
            },
            {
                'callback': on_post_processing,
                'func': lambda call: call.data in ('accept', 'decline', 'accept_error'),
            }
        ]
        self.queries = [
            {
                'callback': on_hashtag_choose,
                'func': lambda call: '#' in call.data
            },
            {
                'callback': send_message_to_group,
                'func': lambda call: call.data == 'end_button'
            },
            {
                'callback': on_post_processing,
                'func': lambda call: call.data in ('accept', 'decline', 'accept_error')
            },
        ]

        self.init()

    def init(self):
        self.register_commands()
        self.register_queries()
        self.add_filters()

    def register_commands(self):
        for command in self.commands:
            self.register_message_handler(pass_bot=True, **command)

    def register_queries(self):
        for query in self.queries:
            self.register_callback_query_handler(pass_bot=True, **query)

    def add_filters(self):
        self.add_custom_filter(asyncio_filters.StateFilter(self))
        self.add_custom_filter(asyncio_filters.IsDigitFilter())

    def start_polling(self):
        log.info("Starting polling...")

        asyncio.run(self.polling(
            non_stop=True,
            skip_pending=True
        ))
