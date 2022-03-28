from aiogram.utils import executor
from aiogram.utils.executor import start_webhook

from telegram_bot.server import dp, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
