import logging
import os

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from cloud_storage.Uploadgram import Uploadgram
from core import MyStates, dp, bot
from social_nets.DownloadYt import DownloadYt


def register_handlers_yt(dispatcher: Dispatcher):
    dispatcher.register_callback_query_handler(callback_yt, lambda c: c.data == 'button_video_yt')
    dispatcher.register_message_handler(message_download_yt, state=MyStates.save_video)


@dp.callback_query_handler(lambda c: c.data == 'button_video_yt')
async def callback_yt(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id,
                           text='Пришлите мне ссылку на видео и я его вам скачаю')
    await MyStates.save_video.set()


@dp.message_handler(state=MyStates.save_video)
async def message_download_yt(message: types.Message, state: FSMContext):
    async with state.proxy():
        user_url = message.text
        await state.finish()
    path_to_file = await DownloadYt().download_video_locally(user_url)
    response = Uploadgram().upload(path_to_file)
    try:
        await bot.send_message(message.from_user.id,
                               text=f"@{message.from_user.username}\n"
                                    f"Ссылка для загрузки {response['url']}?raw")
    except TypeError as te:
        await bot.send_message(message.from_user.id,
                               text=f"@{message.from_user.username}\n"
                                    f"При получении ссылки возникла ошибка")
        logging.info(te.args)
    os.remove(path_to_file)
