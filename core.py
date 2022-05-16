import logging
import os

import sqlite_utils
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from agent.telegram_client import Agent
from states import States

# ---Logging
logging.basicConfig(level=logging.INFO)

# ---Bot
BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)

# ---BotAgent
bot_agent = Agent()

# ---Dispatcher
MyStates = States.States
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# --Database
users_db = sqlite_utils.Database("db/users_db.db")
