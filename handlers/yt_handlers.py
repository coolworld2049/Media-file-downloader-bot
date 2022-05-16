import os

import aiohttp
import emoji
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from cloud_storage.Uploadgram import Uploadgram
from core import MyStates, dp, bot, bot_agent, users_db
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
    path_to_file = await DownloadYt().download_video_locally(message.from_user.id, user_url)
    response = await Uploadgram().upload(path_to_file)
    await bot.send_message(message.from_user.id,
                           text=f"@{message.from_user.username}\n"
                                f"Your download link is {response['url']}")
    users_db[f"{message.from_user.id}_bot_member_files"].upsert(
        {
            "id": 0,
            "url": response['url'],
        }, pk="id")
    os.remove(path_to_file)

    """await bot_agent.start()
    frw_msg = await DownloadYt().download_video_locally(message.from_user.id, user_url)
    await bot_agent.forward_to_bot(frw_msg)
    if message.content_type == 'document':
        await bot.send_message(message.from_user.id, 'received file from agent')
        await bot.send_document(message.from_user.id, message.document.file_id,
                                caption=f"{frw_msg['file_name']}{DownloadYt().ext}")"""


"""@dp.callback_query_handler(lambda c: c.data == 'download_file')
async def callback_download_yt(callback_query: types.CallbackQuery):
    url = users_db[f"{callback_query.from_user.id}_bot_member_files"].get(0).get('url')
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)"""