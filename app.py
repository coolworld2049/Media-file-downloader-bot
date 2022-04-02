from aiogram.utils import executor

from telegram_bot.core import dp
from telegram_bot.handlers.main_handlers import register_handlers_main
from telegram_bot.handlers.vk_handlers import register_handlers_vk

if __name__ == "__main__":
    register_handlers_main(dp)
    register_handlers_vk(dp)

    executor.start_polling(dp, skip_updates=True)
