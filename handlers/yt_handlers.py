import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from virtualenv.util.path import Path

from cloud_storage.Uploadgram import Uploadgram
from core import MyStates, dp, bot
from social_nets.DownloadYt import DownloadYt


def register_handlers_yt(dispatcher: Dispatcher):
    dispatcher.register_callback_query_handler(callback_yt, lambda c: c.data == 'button_video_yt')
    dispatcher.register_message_handler(message_download_yt, state=MyStates.save_video)


@dp.callback_query_handler(lambda c: c.data == 'button_video_yt')
async def callback_yt(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, text='Пришлите ссылку на видео')
    await MyStates.save_video.set()


@dp.message_handler(state=MyStates.save_video)
async def message_download_yt(message: types.Message, state: FSMContext):
    async with state.proxy():
        user_url = message.text
        await state.finish()
    try:
        result = await DownloadYt().download_video_controller(message.from_user.id, user_url)
        path: Path = result[0]
        logging.info(f'user_id: {message.from_user.id}. message_download_yt(): path: {path}')
        if path:
            await bot.send_message(message.from_user.id, text='Загрузка...')
            response = Uploadgram().upload(path)
            await bot.send_message(message.from_user.id,
                                   text=f"@{message.from_user.username}\n"
                                        f"Ссылка для загрузки {response['url']}")
            Path(path).unlink()
    except TypeError as te:
        await bot.send_message(message.from_user.id,
                               text=f"@{message.from_user.username}\n"
                                    f"При получении ссылки возникла ошибка")
        logging.info(te.args)

