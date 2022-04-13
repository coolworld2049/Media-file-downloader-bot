import emoji
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import dp, bot
from db.database import users_db


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_start, commands="start")
    dispatcher.register_message_handler(send_help, commands="help")


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    # display source list
    IK_select_source = InlineKeyboardMarkup(row_width=2)
    IK_select_source.add(InlineKeyboardButton(text=emoji.emojize(':dizzy: Get from Vk'),
                                              callback_data='buttonVk'),
                         InlineKeyboardButton(text=emoji.emojize(':globe_with_meridians: '
                                                                 'Get from YouTube'),
                                              callback_data='button_video_yt'))

    await bot.send_message(message.from_user.id, text='Выберите соц.сеть',
                           reply_markup=IK_select_source)

    users_db["user"].insert_all(
        [
            {
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "language_code": message.from_user.language_code,
                "vk_token": '',
                "vk_user_id": 0,
                "vk_token_expires_in": 0,
                "vk_user_authorized": False,
                "vk_photo_download_completed": False,
                "vk_docs_download_completed": False,
                "number_downloaded_file": 0,
                "y_app_id": '131f4986553d493184f6a5e5af832174',
                "y_api_token": '',
                "ya_user_authorized": False,
                "ya_upload_completed": False,
                "number_uploaded_file": 0
            }
        ], pk="user_id", ignore=True)

    users_db[f"{message.from_user.id}"].create(
        {
            "id": int,
            "photo_url": str,
            "photo_ext": str,
            "album_title": str,
            "docs_url": str,
            "docs_ext": str
        }, pk="id", if_not_exists=True)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/start - выбрать соц. сеть\n'
                         '/help - список команд')
