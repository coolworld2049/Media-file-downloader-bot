import logging
import os

import sqlite_utils
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from states import States

# ---Logging
logging.basicConfig(level=logging.INFO)
fp = open('memory_consumption.log', 'w')

# ---Bot
BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)

# ---Dispatcher
MyStates = States.States
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# --Database
users_db = sqlite_utils.Database("db/users_db.db")
