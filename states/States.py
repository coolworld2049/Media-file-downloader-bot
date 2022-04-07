from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup): # TODO разделить на 3 класса
    auth_vk = State()
    auth_ya_disk = State()
    # vk
    select_vk_scope = State()
    save_all_photo = State()
    save_album = State()
    # yt
    get_video_url = State()
    save_video = State()
