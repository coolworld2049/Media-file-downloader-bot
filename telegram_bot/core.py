import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from cloud_storage.YandexDisk import YandexDisk
from data import ConfigStorage
from data.ConfigStorage import create_file
from social_nets.DownloadVk import DownloadVk
from states import States

# ---Config
config = ConfigStorage.configParser
create_file()

# ---Vk_api
downloadVk = DownloadVk()

# ---Ya_disk_api
yandexDisk = YandexDisk()

# ---Logging
logging.basicConfig(level=logging.INFO)

# ---Bot
BOT_TOKEN = os.environ["BOT_TOKEN"]  # getting a token from the environment!
bot = Bot(token=BOT_TOKEN)

# ---Dispatcher
MyStates = States.States
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# ---Webhooks
HEROKU_APP_NAME = config.get("BOT_DATA", "HEROKU_APP_NAME")

WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = config.get("BOT_DATA", "WEBAPP_PORT")


async def on_startup_webhook(dispatcher: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown_webhook(dispatcher: Dispatcher):
    await bot.delete_webhook()
