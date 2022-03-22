import logging
from os import getenv

from aiogram import Bot, Dispatcher, types

from social_nets.vk_api.auth import auth_user, user_authorized
from social_nets.vk_api.download_from_vk import save_photo, save_by_id, albums_with_photos
from telegram_bot.markup import inline_keyboard_albums_list, inline_keyboard_select_source
from telegram_bot.markup import inline_keyboard_scopes_list

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
                           reply_markup=inline_keyboard_select_source)


@dp.callback_query_handler(lambda c: c.data == 'buttonVk')
async def callback_button_vk(callback_query: types.CallbackQuery):
    global ret_msg
    try:
        ret_msg = auth_user()
        user_authorized = True
    except KeyError as ke:
        ret_msg = ke.args
    finally:
        await bot.send_message(callback_query.from_user.id, ret_msg.__str__())
        await bot.send_message(callback_query.from_user.id, 'Выберите что необходимо скачать',
                               reply_markup=inline_keyboard_scopes_list)


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_select_album(callback_query: types.CallbackQuery):
    print(user_authorized)
    if user_authorized:
        await bot.send_message(callback_query.from_user.id,
                               text='Список фотоальбомов, доступных для скачивания',
                               reply_markup=inline_keyboard_albums_list)
        save_by_id()
