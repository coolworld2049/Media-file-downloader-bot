from aiogram.utils import executor

from telegram_bot.server import dp

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
