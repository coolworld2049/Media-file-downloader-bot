import emoji
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import dp, bot


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_start, commands="start")
    dispatcher.register_message_handler(send_help, commands="help")


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    # display source list
    IK_select_source = InlineKeyboardMarkup(row_width=2)
    IK_select_source.add(InlineKeyboardButton(text=emoji.emojize(':dizzy: Download from Vk'),
                                              callback_data='buttonVk'),
                         InlineKeyboardButton(text=emoji.emojize(':globe_with_meridians: '
                                                                 'Download from YouTube'),
                                              callback_data='button_video_yt'),
                         InlineKeyboardButton(text=emoji.emojize(':framed_picture: '
                                                                 'Download photo from Pinterest'),
                                              callback_data='button_music_yt'))

    await bot.send_message(message.from_user.id, text='Выберите соц. сеть',
                           reply_markup=IK_select_source)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/start - выбрать соц. сеть\n'
                         '/help - список команд')
