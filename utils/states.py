from telebot.asyncio_handler_backends import State, StatesGroup

class MyStates(StatesGroup):
    # Just name variables differently
    on_button_choose = State() # creating instances of State class is enough from now
    on_hashtag_add = State()
    on_ps_add = State()
    on_hashtag_delete = State()
    on_decline = State()