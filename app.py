import os

from aiogram import Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

from handlers.cloud_storage_handlers import register_cloud_storage
from handlers.start_handler import register_handlers_main
from handlers.vk_handlers import register_handlers_vk
from handlers.yt_handlers import register_handlers_yt

# ---Bot
bot = Bot(token=os.environ["BOT_TOKEN"])

# ---Dispatcher
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


def on_startup(dispatcher):
    register_handlers_main(dispatcher)
    register_cloud_storage(dispatcher)
    register_handlers_vk(dispatcher)
    register_handlers_yt(dispatcher)


def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup(dp))


if __name__ == "__main__":
    main()