""" States machine module """
from telebot.asyncio_handler_backends import State, StatesGroup


class MyStates(StatesGroup):  # pylint: disable=too-few-public-methods
    """ Just name variables differently """
    on_start_button_choose = State()  # creating instances of State class is enough from now
    on_hashtag_add = State()
    on_sign_add = State()
    on_hashtag_delete = State()
    on_decline = State()
    on_send_new_post_to_group = State()
