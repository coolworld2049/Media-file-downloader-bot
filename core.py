import logging
import os
import sqlite3

import sqlite_utils
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from states import States

# ---Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('log.log', encoding="utf-8")
stream_handler = logging.StreamHandler()

stream_formatter = logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s')
file_formatter = logging.Formatter("{'time':'%(asctime)s', 'name': '%(name)s', "
                                   "'level': '%(levelname)s', 'message': '%(message)s'}")
stream_handler.setFormatter(stream_formatter)
file_handler.setFormatter(file_formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# ---Database
path_to_db = 'db/users_db'
# sqlite3.connect(path_to_db)
users_db = sqlite_utils.Database(path_to_db)

# ---Bot
BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)

# ---Dispatcher
MyStates = States.States
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
