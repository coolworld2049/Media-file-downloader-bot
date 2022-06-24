from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup):
    # auth
    auth_vk = State()
    auth_ya_disk = State()
    # upload_user_file
    upload_user_file = State()
    # vk
    select_vk_scope = State()
    select_storage = State()
    save_album = State()
    # yt
    save_video = State()
