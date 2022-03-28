from aiogram.utils.executor import start_webhook

from telegram_bot.server import dp, WEBHOOK_PATH, on_startup, on_shutdown, WEBAPP_HOST, WEBAPP_PORT

if __name__ == "__main__":

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=False,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
