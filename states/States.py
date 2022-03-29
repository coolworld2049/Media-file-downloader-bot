from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup):
    callback_auth_link = State()
    auth_ya_disk = State()
    token_ya_disk = State()



