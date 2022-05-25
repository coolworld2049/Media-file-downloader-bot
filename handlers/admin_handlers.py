import os

from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import dp, bot
from db.db_mgmt import export_db


def register_admin_handlers(dispatcher: Dispatcher):
    dispatcher.register_message_handler(admin, commands=['admin'])


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if message.from_user.id == os.environ["ADMIN_ID"]:
        IK_admin = InlineKeyboardMarkup(row_width=2)
        IK_admin.add(InlineKeyboardButton(text='statistics', callback_data='statistics'))
        await bot.send_message(message.from_user.id, text=f'Admin panel',
                               reply_markup=IK_admin)


@dp.callback_query_handler(lambda c: c.data == 'statistics')
async def bot_statistics(callback_query: types.CallbackQuery):
    path = export_db(callback_query.from_user)
    file = open(path, 'rb')
    await bot.send_document(callback_query.from_user.id, file)
    os.remove(path)
