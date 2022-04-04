from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup):
    auth_vk = State()
    auth_ya_disk = State()
    select_vk_scope = State()
    save_album = State()
    save_docs = State()
