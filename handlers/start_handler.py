from datetime import datetime

import emoji
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, User

from core import dp, bot, users_db, logger
from db.export_table import export_csv


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_start, commands="start")
    dispatcher.register_message_handler(send_help, commands="help")


async def add_user_to_db(user: User):
    """:param user: message.from_user"""
    users_db["user"].insert_all(
        [
            {
                "user_id": user.id,
                "language_code": user.language_code,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_url": user.url,
                "last_seen": datetime.timestamp(datetime.now()),
                "cloud_storage": '',
                "auth_attempts": 3,
                "vk_token": '',
                "vk_user_id": 0,
                "vk_token_expires_in": 0,
                "vk_user_authorized": False,
                "vk_photo_download_completed": False,
                "vk_docs_download_completed": False,
                "total_number_downloaded_file": 0,
                "y_api_token": '',
                "ya_user_authorized": False,
                "ya_upload_completed": False,
                "total_number_uploaded_file": 0
            }
        ], pk="user_id", ignore=True)

    users_db['user'].upsert(
        {
            "user_id": user.id,
            "language_code": user.language_code,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_url": user.url,
            "last_seen": datetime.timestamp(datetime.now()),
            "auth_attempts": 3
        }, pk="user_id")

    users_db[f"{user.id}_calls"].create(
        {
            "id": int,
            "settable_state": str,
            "call_from": str,
        }, pk="id", if_not_exists=True)

    users_db[f"{user.id}_photos"].create(
        {
            "id": int,
            "photo_url": str,
            "photo_ext": str,
            "album_title": str,
        }, pk="id", if_not_exists=True)

    users_db[f"{user.id}_docs"].create(
        {
            "id": int,
            "docs_url": str,
            "docs_ext": str,
            "title": str
        }, pk="id", if_not_exists=True)


async def delete_user_tables(user: User):
    """:param user: message.from_user"""
    users_db.conn.execute(f"DELETE FROM user WHERE user_id = {user.id}")
    users_db[f"{user.id}_calls"].drop()
    users_db[f"{user.id}_photos"].drop()
    users_db[f"{user.id}_docs"].drop()


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    if not users_db['user'].get(message.from_user.id).get('user_id'):
        logger.info(f'user_id:{message.from_user.id} добавлен в базу данных')
        await add_user_to_db(message.from_user)
    time_diff_visit = \
        users_db['user'].get(message.from_user.id).get('last_seen') - datetime.timestamp(datetime.now())
    if abs(time_diff_visit) // 60 >= 1:  # last seen 2h ago
        await export_csv(message.from_user)
        await delete_user_tables(message.from_user)
        await add_user_to_db(message.from_user)
        logger.info(f'user_id: {message.from_user.id} db data overwritten because more than 2 hours have\n'
                     f' passed since the last launch of the bot')

    IK_select_source = InlineKeyboardMarkup(row_width=2)
    IK_select_source.add(
        InlineKeyboardButton(text=emoji.emojize(':dizzy: Get from VK'),
                             callback_data='buttonVk'),
        InlineKeyboardButton(text=emoji.emojize(':globe_with_meridians: Get from YouTube'),
                             callback_data='button_video_yt'))
    await bot.send_message(message.from_user.id, text=f'Привет {message.from_user.first_name}!',
                           reply_markup=IK_select_source)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/start - выбрать соц. сеть\n',
                         '/help - список команд')
