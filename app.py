from aiogram.utils import executor

from core import dp
from handlers.user.start_handler import register_handlers_main
from handlers.user.vk_handlers import register_handlers_vk
from handlers.user.yt_handlers import register_handlers_yt

if __name__ == "__main__":
    register_handlers_main(dp)
    register_handlers_vk(dp)
    register_handlers_yt(dp)

    executor.start_polling(dp, skip_updates=True)
