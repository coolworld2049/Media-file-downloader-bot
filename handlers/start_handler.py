from datetime import datetime

import emoji
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import users_db, logger, dp, bot
from db.db_mgmt import export_db, __create_user_table, __add_user_to_db, __delete_user_tables


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_start, commands="start")
    dispatcher.register_message_handler(send_help, commands="help")


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    __create_user_table()
    __add_user_to_db(message.from_user)
    logger.info(f'user_id:{message.from_user.id} added to db')

    time_diff_visit = \
        users_db['user'].get(message.from_user.id).get('last_seen') - datetime.timestamp(datetime.now())
    if abs(time_diff_visit) // 60 >= 120:  # last seen 2h ago
        export_db(message.from_user)
        __delete_user_tables(message.from_user)
        __add_user_to_db(message.from_user)
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
