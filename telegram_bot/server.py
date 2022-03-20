import logging

from os import getenv

from aiogram import Bot, Dispatcher, types

bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Error: no token provided")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_start(message: types.Message):
    await message.reply('Привет!\n\n'
                        'Это бот для загрузки ваших  медиафайлов из социальных сетей.\n\n'
                        'Сейчас доступна загрузка из Vk, YouTube\n\n'
                        'Список команд:\n'
                        '\t/select - выбрать соц. сеть\n'
                        '\t/help - список команд')


@dp.message_handler(commands=['select'])
async def send_select(message: types.Message):
    await bot.send_message(message.from_user.id, 'asd')
