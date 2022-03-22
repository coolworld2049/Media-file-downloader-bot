import logging
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from social_nets.DownloadVk import DownloadVk

# ---bot
bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Error: no token provided")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

# ---vk_api
downloadVk = DownloadVk()


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
    # display source list
    IK_select_source = InlineKeyboardMarkup()

    inline_buttonVk = InlineKeyboardButton('Vk', callback_data='buttonVk')
    inline_buttonYt = InlineKeyboardButton('YouTube', callback_data='buttonYt')
    IK_select_source.add(inline_buttonVk, inline_buttonYt)

    await bot.send_message(message.from_user.id, text='Выберите соц. сеть',
                           reply_markup=IK_select_source)


@dp.callback_query_handler(lambda c: c.data == 'buttonVk')
async def callback_button_vk(callback_query: types.CallbackQuery):
    global ret_msg

    # display scopes list
    IK_scopes_list = InlineKeyboardMarkup()

    scopes_str = downloadVk.scopes.split(',')
    for scope in scopes_str:
        IK_scopes_list.add(InlineKeyboardButton(f'{scope}', callback_data=f'{scope}'))

    try:
        ret_msg = downloadVk.auth_user()
    except Exception as e:
        ret_msg = e.args
    finally:
        await bot.send_message(callback_query.from_user.id, ret_msg)
        await bot.send_message(callback_query.from_user.id, 'Выберите что необходимо скачать',
                               reply_markup=IK_scopes_list)


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_select_album(callback_query: types.CallbackQuery):
    # display albums list
    print(downloadVk.user_authorized)
    IK_albums_list = InlineKeyboardMarkup()
    if downloadVk.user_authorized:
        for album in downloadVk.display_albums():
            IK_albums_list.add(InlineKeyboardButton(f'{album}', callback_data=f'{album}'))

    if downloadVk.user_authorized:
        await bot.send_message(callback_query.from_user.id,
                               text='Список фотоальбомов, доступных для скачивания',
                               reply_markup=IK_albums_list)
        downloadVk.save_by_id()


if __name__ == "__main__":
    executor.start_polling(dp)

