from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from core import MyStates, dp, bot
from social_nets.DownloadYt import DownloadYt


def register_handlers_yt(dispatcher: Dispatcher):
    dispatcher.register_message_handler(message_download_yt, state=MyStates.save_video)


@dp.callback_query_handler(lambda c: c.data == 'button_video_yt')
async def callback_yt(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id,
                           text='Пришлите мне ссылку на видео и я его вам скачаю')
    await MyStates.save_video.set()


@dp.message_handler(state=MyStates.save_video)
async def message_download_yt(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['callback_url'] = message.text
        user_url = data['callback_url']
        await state.finish()
    print(f'downloading {user_url}')
    video_name = await DownloadYt().download_file(user_url)
    video_ext = '.' + video_name.split('.')[1]
    video_title = video_name.split('.')[0]
    with open(f'temp/{video_title}{video_ext}', 'rb') as video:
        await bot.send_video(message.from_user.id, video)
    await DownloadYt().delete_temp(video_title)
