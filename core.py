import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from cloud_storage.YandexDisk import YandexDisk
from data import config
from data.config import create_file
from social_nets.DownloadVk import DownloadVk
from social_nets.DownloadYt import DownloadYt
from states import States

# ---Config
config = config.configParser
create_file()

# ---Vk_api
downloadVk = DownloadVk()

# ---Vk_api
downloadYt = DownloadYt()

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

