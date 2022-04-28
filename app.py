from aiogram.utils import executor

from core import dp
from handlers.start_handler import register_handlers_main
from handlers.vk_handlers import register_handlers_vk
from handlers.yt_handlers import register_handlers_yt


def on_startup():
    register_handlers_main(dp)
    register_handlers_vk(dp)
    register_handlers_yt(dp)


def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup())


if __name__ == "__main__":
    # setup.setup_py()
    main()
