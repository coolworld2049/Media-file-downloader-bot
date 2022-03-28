import os

from aiogram.utils import executor
from aiogram.utils.executor import start_webhook

from telegram_bot.server import dp, bot, BOT_TOKEN

if __name__ == "__main__":
    # executor.start_polling(dp, skip_updates=True)

    HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

    # webhook settings
    WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
    WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
    WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

    # webserver settings
    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = os.getenv('PORT', default=8000)


    async def on_startup(dispather):
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


    async def on_shutdown(dispather):
        await bot.delete_webhook()


    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=False,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
