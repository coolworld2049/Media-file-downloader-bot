import emoji
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from core import dp, bot, MyStates, users_db
from handlers.vk_handlers import goto_select_vk_scope
from social_nets.DownloadVk import DownloadVk


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_start, commands="start")
    dispatcher.register_message_handler(send_select, commands="select")
    dispatcher.register_message_handler(send_help, commands="help")


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    # await DownloadYt().download_file()

    await bot.send_message(message.from_user.id, text=f'Привет {message.from_user.first_name}!'
                                                      f' Для загрузки фото и документов из вк'
                                                      ' необходимо авторизоваться в вк и выбрать место,'
                                                      ' куда будут загружены ваши фотографии',
                           reply_markup=ReplyKeyboardRemove())
    # display source list
    IK_select_source = InlineKeyboardMarkup(row_width=2)
    IK_select_source.add(InlineKeyboardButton(text=emoji.emojize(':dizzy: Get from Vk'),
                                              callback_data='buttonVk'),
                         InlineKeyboardButton(text=emoji.emojize(':globe_with_meridians: '
                                                                 'Get from YouTube'),
                                              callback_data='button_video_yt'))

    await bot.send_message(message.from_user.id, text='Выбери соц.сеть',
                           reply_markup=IK_select_source)

    users_db["user"].insert_all(
        [
            {
                "user_id": message.from_user.id,
                "language_code": message.from_user.language_code,
                "username": message.from_user.username,
                "last_name": message.from_user.last_name,
                "first_name": message.from_user.first_name,
                "user_url": message.from_user.url,
                "vk_token": '',
                "vk_user_id": 0,
                "vk_token_expires_in": 0,
                "vk_user_authorized": False,
                "vk_photo_download_completed": False,
                "vk_docs_download_completed": False,
                "number_downloaded_file": 0,
                "y_api_token": '',
                "ya_user_authorized": False,
                "ya_upload_completed": False,
                "number_uploaded_file": 0
            }
        ], pk="user_id", ignore=True)

    users_db[f"{message.from_user.id}_photos"].create(
        {
            "id": int,
            "photo_url": str,
            "photo_ext": str,
            "album_title": str,
        }, pk="id", if_not_exists=True)

    users_db[f"{message.from_user.id}_docs"].create(
        {
            "id": int,
            "docs_url": str,
            "docs_ext": str,
            "title": str
        }, pk="id", if_not_exists=True)

    if not await DownloadVk().check_token(message.from_user.id):
        users_db["user"].upsert(
            {
                "user_id": message.from_user.id,
                "vk_user_authorized": False
            }, pk="user_id")


@dp.message_handler(commands='/select')
async def send_select(message: types.Message):
    await bot.send_message(message.from_user.id,
                           text='Перейти к выбору области загрузки',
                           reply_markup=goto_select_vk_scope())
    await MyStates.select_vk_scope.set()


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/start - выбрать соц. сеть\n'
                         '/select - перейти к скачиванию с вк'
                         '/help - список команд')
