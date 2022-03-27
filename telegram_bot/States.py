from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup):
    callback_auth_link: State = State()
    callback_album_id: State = State()


