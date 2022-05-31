import os

from aiogram.utils.executor import start_webhook

from core import dp, bot
from handlers.admin_handlers import register_admin_handlers
from handlers.cloud_storage_handlers import register_cloud_storage
from handlers.start_handler import register_handlers_main
from handlers.vk_handlers import register_handlers_vk
from handlers.yt_handlers import register_handlers_yt

WEBHOOK_HOST = f'{os.environ["WEBHOOK_HOST"]}:80'
WEBHOOK_PATH = f'/{os.environ["BOT_TOKEN"]}/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '0.0.0.0'  # or ip
WEBAPP_PORT = WEBHOOK_HOST.split(':')[-1]


async def on_startup(dispather):
    register_admin_handlers(dp)
    register_handlers_main(dp)
    register_cloud_storage(dp)
    register_handlers_vk(dp)
    register_handlers_yt(dp)
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispather):
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
