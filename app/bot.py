""" Bot class module """
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.util import content_type_media
from telebot import asyncio_filters
from utils.states import MyStates
from utils.logger import log
from handlers.group import on_message_received
from handlers.private import on_hashtag_choose, send_post_to_group, on_post_processing
from handlers.admin_configs import (cmd_add_hashtag,
                                    cmd_add_admin,
                                    cmd_remove_admin,
                                    cmd_remove_hashtag,
                                    cmd_add_sign)


from handlers.admin_commands import (on_send_new_post_to_group, get_commands_markup,
                                     on_button_choose,
                                     on_hashtag_add,
                                     on_sign_add,
                                     on_hashtag_delete)


class Bot(AsyncTeleBot):
    """ Bot class """

    def __init__(self, config, **kwargs):
        self.config = config
        super().__init__(self.config['TOKEN'], **kwargs, parse_mode='HTML')
        self.commands = [
            # Admin handlers
            {
                'callback': cmd_remove_hashtag,
                'commands': 'remove_hashtag',
                'chat_types': 'private',
            },
            {
                'callback': cmd_remove_admin,
                'commands': 'remove_admin',
                'chat_types': 'private',
            },
            {
                'callback': cmd_add_admin,
                'content_types': 'contact',
                'chat_types': 'private',
            },
            {
                'callback': cmd_add_hashtag,
                'commands': 'add_hashtag',
                'chat_types': 'private',
            },
            {
                'callback': cmd_add_sign,
                'commands': 'add_sign',
                'chat_types': 'private',
            },
            # Admin button handlers
            {
                'callback': get_commands_markup,
                'commands': 'start',
                'chat_types': 'private',
            },
            {
                'callback': on_button_choose,
                'state': MyStates.on_button_choose,
                'chat_types': 'private',
            },
            {
                'callback': on_hashtag_add,
                'state': MyStates.on_hashtag_add,
                'chat_types': 'private',
            },
            {
                'callback': on_hashtag_delete,
                'state': MyStates.on_hashtag_delete,
                'chat_types': 'private',
            },
            {
                'callback': on_sign_add,
                'state': MyStates.on_sign_add,
                'chat_types': 'private',
            },
            {
                'callback': on_send_new_post_to_group,
                'state': MyStates.on_send_new_post_to_group,
                'content_types': content_type_media,
                'chat_types': 'private',
            },
            # Basic handlers
            {
                'callback': on_message_received,
                'content_types': content_type_media,
            },
        ]
        self.queries = [
            {
                'callback': on_hashtag_choose,
                'func': lambda call: '#' in call.data
            },
            {
                'callback': send_post_to_group,
                'func': lambda call: call.data == 'end_button'
            },
            {
                'callback': on_post_processing,
                'func': lambda call: '/post_processing' in call.data
            },
        ]

        self.init()

    def init(self):
        """ Init bot

        Register commands, queries, filters
        """
        self.register_commands()
        self.register_queries()
        self.add_filters()

    def register_commands(self):
        """ Register bot message commands

        Cycle through self.commands list and register each command"""
        for command in self.commands:
            self.register_message_handler(pass_bot=True, **command)
        log.info("Commands registered")

    def register_queries(self):
        """ Register bot queries

        Cycle through self.queries list and register each query"""
        for query in self.queries:
            self.register_callback_query_handler(pass_bot=True, **query)
        log.info("Queries registered")

    def add_filters(self):
        """ Bot class module

        This module contains Bot class, which is used to create bot instance
        """

        self.add_custom_filter(asyncio_filters.StateFilter(self))
        self.add_custom_filter(asyncio_filters.IsDigitFilter())
        log.info("Filters added")

    def start_polling(self):
        """ Start polling

        Start polling and run event loop
        """
        log.info("Starting polling...")
        asyncio.run(self.polling(
            non_stop=True,
            skip_pending=True
        ))
