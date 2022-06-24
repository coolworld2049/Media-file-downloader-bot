from datetime import datetime

import emoji
import sqlite_utils
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import users_db, logger, dp, bot
from db.db_mgmt import export_db, add_user_to_db, delete_user_tables, create_user_table


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(message_start, commands="start")
    dispatcher.register_message_handler(send_help, commands="help")
    dispatcher.register_callback_query_handler(message_start_menu, lambda c: c.data == 'to_menu')


@dp.message_handler(commands=['start'])
async def message_start(message: types.Message):
    create_user_table()
    try:
        if users_db['user'].get(message.from_user.id).get('user_id'):
            time_delta = users_db['user'].get(message.from_user.id).get('last_seen') - \
                         datetime.timestamp(datetime.now())
            if time_delta and abs(time_delta) // 60 >= 120:  # last seen 2h ago
                export_db(message.from_user)
                delete_user_tables(message.from_user)
                add_user_to_db(message.from_user)
                logger.info(f'user_id: {message.from_user.id} db data overwritten because '
                            f'more than 2 hours have passed since the last launch of the bot')
    except sqlite_utils.db.NotFoundError:
        add_user_to_db(message.from_user)
        logger.info(f'user_id:{message.from_user.id} added to db')

    IK_select_source = InlineKeyboardMarkup(row_width=2)
    IK_select_source.add(
        InlineKeyboardButton(text=f"{emoji.emojize(':dizzy:')} Загрузить из ВК",
                             callback_data='buttonVk'),
        InlineKeyboardButton(text=f"{emoji.emojize(':globe_with_meridians:')} Загрузить из Youtube",
                             callback_data='button_video_yt'))
    await bot.send_message(message.from_user.id, text=f'Привет {message.from_user.first_name}!',
                           reply_markup=IK_select_source)


@dp.callback_query_handler(lambda c: c.data == 'start_menu')
async def message_start_menu(callback_query: types.CallbackQuery):
    IK_select_source = InlineKeyboardMarkup(row_width=2)
    IK_select_source.add(
        InlineKeyboardButton(text=emoji.emojize(':dizzy: Загрузить из ВК'),
                             callback_data='buttonVk'),
        InlineKeyboardButton(text=emoji.emojize(':globe_with_meridians: Загрузить из Youtube'),
                             callback_data='button_video_yt'))
    await bot.send_message(callback_query.from_user.id,
                           text=f'Меню',
                           reply_markup=IK_select_source)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/start' + '- выбрать соц. сеть\n'
                                    '/help' + '- список команд')
