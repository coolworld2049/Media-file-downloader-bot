import logging
import os
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from social_nets.DownloadVk import DownloadVk
from telegram_bot import States

# ---bot
logging.basicConfig(level=logging.INFO)

bot_token = getenv("BOT_TOKEN")
storage = MemoryStorage()
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

bot.delete_webhook()
bot.set_webhook(url=os.getenv('API_URL'))
"""server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
"""
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
    send_link = downloadVk.send_auth_link()
    await bot.send_message(callback_query.from_user.id,
                           text=f'Это ссылка для авторизации в вашем аккаунте.'
                                f' Нажмите на ссылку и скопируйте адрес из адресной'
                                f' строки в открывшемся окне браузера и нажмите на кнопку'
                                f' "Вставить" в меню:    {send_link}')
    await States.States.callback_auth_link.set()  # start FSM machine


@dp.message_handler(state=States.States.callback_auth_link)
async def bot_auth_vk(message: types.Message, state: FSMContext):
    downloadVk.auth_vk(message.text)

    if downloadVk.user_authorized:
        await bot.send_message(message.from_user.id, 'Вы авторизованы!')
        if downloadVk.user_authorized:
            # display scopes list
            IK_scopes_list = InlineKeyboardMarkup()
            scopes_str = downloadVk.scopes.split(',')
            for scope in scopes_str:
                IK_scopes_list.add(InlineKeyboardButton(f'{scope}', callback_data=f'{scope}'))
            await bot.send_message(message.from_user.id, 'Выберите что необходимо скачать',
                                   reply_markup=IK_scopes_list)
    else:
        await bot.send_message(message.from_user.id, 'Ошибка авторизации!')
        await send_select()

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_photos(callback_query: types.CallbackQuery):
    # display albums list
    IK_albums_list = InlineKeyboardMarkup()
    if downloadVk.user_authorized:
        album_list = downloadVk.display_albums()
        for a_id, title in album_list:
            IK_albums_list.add(InlineKeyboardButton(f'{title}', callback_data=str(a_id)))
        await bot.send_message(callback_query.from_user.id,
                               text='Список фотоальбомов, доступных для скачивания',
                               reply_markup=IK_albums_list)
    else:
        await bot.send_message(callback_query.from_user.id, text='Вы не авторизованы')


@dp.callback_query_handler(lambda c: c.data)
async def callback_save_album(callback_query: types.CallbackQuery):
    items = downloadVk.display_albums_id()
    sel_album = callback_query.data
    for item in items:
        if item == int(sel_album):
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Загрузка альбома {downloadVk.display_albums_title(item)}')
            downloadVk.save_photo_by_id(int(sel_album))
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Альбом {downloadVk.display_albums_title(item)} загружен')
            break
