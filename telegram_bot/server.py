import json
import logging
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from social_nets.DownloadVk import DownloadVk

# ---bot
logging.basicConfig(level=logging.INFO)

bot_token = getenv("BOT_TOKEN")
storage = MemoryStorage()
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# ---vk_api
downloadVk = DownloadVk()
save_selected_album: int


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
    auth_msg = downloadVk.auth_user()
    await bot.send_message(callback_query.from_user.id, auth_msg)

    # display scopes list
    IK_scopes_list = InlineKeyboardMarkup()
    scopes_str = downloadVk.scopes.split(',')
    for scope in scopes_str:
        IK_scopes_list.add(InlineKeyboardButton(f'{scope}', callback_data=f'{scope}'))
    await bot.send_message(callback_query.from_user.id, 'Выберите что необходимо скачать',
                           reply_markup=IK_scopes_list)


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_select_album(callback_query: types.CallbackQuery):
    # display albums list
    IK_albums_list = InlineKeyboardMarkup()
    if downloadVk.user_authorized:
        album_list = downloadVk.display_albums()
        for a_id, title, count in album_list:
            IK_albums_list.add(InlineKeyboardButton(f'{count}.'f'{title}', callback_data=str(a_id)))
            count += 1
        await bot.send_message(callback_query.from_user.id,
                               text='Список фотоальбомов, доступных для скачивания',
                               reply_markup=IK_albums_list)
    else:
        await bot.send_message(callback_query.from_user.id, text='Вы не авторизованы', )


@dp.callback_query_handler(lambda c: c.data == '281175201')
async def callback_select_album(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, text=f'Загрузка альбома {callback_query.data}')
    downloadVk.save_photo_by_id(int(callback_query.data))


if __name__ == "__main__":
    executor.start_polling(dp)

    """list1 = [[281821142, 457248715],
             [281821751, 457248714],
             [281175201, 457248684],
             [281175201, 457248683],
             [281175201, 457248677],
             [281175201, 457248676],
             [281175201, 457248675],
             [281175201, 457248674],
             [281175201, 457248662],
             [281175201, 457248660],
             [281175201, 457248659],
             [281175201, 457248658],
             [281175201, 457248657],
             [281175201, 457248655],
             [281175201, 457248653],
             [281175201, 457248652],
             [281175201, 457248650],
             [281175201, 457248649]]

    list2 = [[281821142],
             [281821751],
             [281175201]]"""
