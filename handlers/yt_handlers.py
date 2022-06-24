from pathlib import Path
from typing import Any

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from cloud_storage.UploadgramApi import UploadgramApi
from core import MyStates, dp, bot, logger
from handlers.start_handler import message_start_menu, message_start
from social_nets.DownloadYt import DownloadYt


def register_handlers_yt(dispatcher: Dispatcher):
    dispatcher.register_callback_query_handler(callback_yt, lambda c: c.data == 'button_video_yt')
    dispatcher.register_message_handler(message_download_yt, state=MyStates.save_video)
    dispatcher.register_callback_query_handler(callback_yt_get_video,
                                               lambda c: c.data == 'yt_get_video' or 'yt_get_audio')


@dp.callback_query_handler(lambda c: c.data == 'button_video_yt')
async def callback_yt(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, text='Пришлите ссылку на видео')
    await MyStates.save_video.set()


@dp.message_handler(state=MyStates.save_video)
async def message_download_yt(message: types.Message, state: FSMContext):
    IK_button_yt = InlineKeyboardMarkup()
    async with state.proxy() as data:
        if message.text.startswith(tuple(['https://www.youtube.com', 'https://youtu.be'])):
            data['user_url'] = message.text
            await state.finish()
            IK_button_yt.add(InlineKeyboardButton('Видео', callback_data='yt_get_video'),
                             InlineKeyboardButton('Аудио', callback_data='yt_get_audio'))
            await bot.send_message(message.from_user.id, text='Выберите тип загрузки',
                                   reply_markup=IK_button_yt)
        elif message.text == '/start':
            await state.finish()
            await message_start(message)
        else:
            await state.finish()
            await MyStates.save_video.set()
            await bot.send_message(message.from_user.id, text='Неверный формат ссылки')


@dp.callback_query_handler(lambda c: c.data == 'yt_get_video' or 'yt_get_audio')
async def callback_yt_get_video(callback_query: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    url = state_data['user_url']
    if callback_query.data == 'yt_get_video':
        await bot.send_message(callback_query.from_user.id,
                               text='Загрузка видео началась.'
                                    ' Когда видео будет доступно для скачивания бот уведомит вас ')
        res = await DownloadYt(callback_query.from_user.id, url).download_video()
        if res:
            await upload_to_cloud(res, callback_query)
    elif callback_query.data == 'yt_get_audio':
        await bot.send_message(callback_query.from_user.id,
                               text='Загрузка аудио началась.'
                                    ' Когда аудио будет доступно для скачивания бот уведомит вас ')
        res = await DownloadYt(callback_query.from_user.id, url).download_audio()
        if res:
            await upload_to_cloud(res, callback_query)


async def upload_to_cloud(path: Any, callback_query: types.CallbackQuery):
    path = Path(path)
    if path:
        try:
            response = UploadgramApi().upload(path)
            await bot.send_message(callback_query.from_user.id,
                                   text=f"@{callback_query.from_user.username}\n"
                                        f"Ссылка для загрузки {response['url']}")
        except TypeError as te:
            logger.info(f'user_id: {callback_query.from_user.id}.'
                        f' message_download_yt(): TypeError: {te.args}')
            await bot.send_message(callback_query.from_user.id,
                                   text=f"@{callback_query.from_user.username}\n"
                                        f"Uploadgram.me currently unavailable."
                                        f" Please, try again later.")
        finally:
            logger.info(f'user_id: {callback_query.from_user.id}.'
                        f' message_download_yt(): path: {path}')
    elif not path:
        await bot.send_message(callback_query.from_user.id,
                               text=f"@{callback_query.from_user.username}\n"
                                    f"При получении ссылки возникла ошибка")
        logger.info(f'callback_yt_get_video(user_id: {callback_query.from_user.id}):'
                    f' path: Path is empty')
    Path(path).unlink() if Path(path).exists() else None
    await message_start_menu(callback_query)
