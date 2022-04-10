import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware


from states import States

# ---Logging
logging.basicConfig(level=logging.INFO)

# ---Bot
BOT_TOKEN = os.environ["BOT_TOKEN"]  # getting a token from the environment!
bot = Bot(token=BOT_TOKEN)

# ---Dispatcher
MyStates = States.States

dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

