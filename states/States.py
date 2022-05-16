from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup):
    # start
    start_bot = State()
    # auth
    auth_vk = State()
    auth_ya_disk = State()
    # upload_user_file
    upload_user_file = State()
    # vk
    select_vk_scope = State()
    select_storage = State()
    save_all_photo = State()
    save_album = State()
    # yt
    get_video_url = State()
    save_video = State()
