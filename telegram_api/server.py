import logging
from os import getenv

from aiogram import Bot, Dispatcher, types


bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Error: no token provided")

bot = Bot(token=bot_token)

logging.basicConfig(level=logging.INFO)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer(
        "Бот для загрузки данных из социальных сетей\n\n"
        "Выбрать соц.сеть: /select\n")
