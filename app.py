from aiogram.utils import executor

from core import dp
from handlers.admin_handlers import register_admin_handlers
from handlers.cloud_storage_handlers import register_cloud_storage
from handlers.start_handler import register_handlers_main
from handlers.vk_handlers import register_handlers_vk
from handlers.yt_handlers import register_handlers_yt


def on_startup(dispatcher):
    register_admin_handlers(dispatcher)
    register_handlers_main(dispatcher)
    register_cloud_storage(dispatcher)
    register_handlers_vk(dispatcher)
    register_handlers_yt(dispatcher)


def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup(dp))


if __name__ == "__main__":
    main()
