import logging
from os import getenv

from aiogram import Bot, Dispatcher, types

from telegram_bot.markup import inline_keyboard
from social_nets.vk_api.auth import auth_user

bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Error: no token provided")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    await message.answer('Привет!\n\n'
                         'Это бот для загрузки ваших  медиафайлов из социальных сетей.\n\n'
                         'Сейчас доступна загрузка из Vk, YouTube\n\n'
                         'Список команд:\n'
                         '\t/select - выбрать соц. сеть\n'
                         '\t/help - список команд')


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/select - выбрать соц. сеть\n'
                         '/help - список команд')


@dp.message_handler(commands=['select'])
async def send_select(message: types.Message):
    await bot.send_message(message.from_user.id, text='Выберите соц. сеть',
                           reply_markup=inline_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'buttonVk')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Enter your access_token(copy from the"
                                                        " address bar in the window that opens):\n")
    auth_user()
