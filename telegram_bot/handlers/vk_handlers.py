from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_bot.core import dp, downloadVk, bot, yandexDisk


def register_handlers_vk(dp: Dispatcher):
    dp.register_message_handler(message_select_vk_scope, commands="continue_on_vk")
    dp.register_callback_query_handler(callback_photos, lambda c: c.data == 'photos')
    dp.register_callback_query_handler(callback_save_album, lambda c: c.data)


@dp.message_handler(commands=['continue_on_vk'])
async def message_select_vk_scope(message: types.Message):
    if downloadVk.user_authorized and yandexDisk.user_authorized:
        # display scopes list
        IK_scopes_list = InlineKeyboardMarkup()
        scopes_str = downloadVk.scopes.split(',')
        for scope in scopes_str:
            IK_scopes_list.add(InlineKeyboardButton(f'{scope}', callback_data=f'{scope}'))

        await bot.send_message(message.from_user.id, 'Выберите что необходимо скачать',
                               reply_markup=IK_scopes_list)


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_photos(callback_query: types.CallbackQuery):
    # display albums list
    IK_albums_list = InlineKeyboardMarkup()
    album_list = downloadVk.display_albums()
    for a_id, title in album_list:
        IK_albums_list.add(InlineKeyboardButton(f'{title}', callback_data=str(a_id)))
    await bot.send_message(callback_query.from_user.id,
                           text='Список фотоальбомов, доступных для скачивания',
                           reply_markup=IK_albums_list)


@dp.callback_query_handler(lambda c: c.data)
async def callback_save_album(callback_query: types.CallbackQuery):
    try:
        items = downloadVk.display_albums_id()
        sel_album = callback_query.data
        for item in items:
            if item == int(sel_album):
                await bot.send_message(callback_query.from_user.id,
                                       text=f'Загрузка альбома {downloadVk.display_albums_title(item)}')
                downloadVk.save_photo_by_id(int(sel_album))
                await bot.send_message(callback_query.from_user.id,
                                       text=f'Альбом {downloadVk.display_albums_title(item)} загружен')

                """if downloadVk.loading_complete:
                    for photo in downloadVk.photo_url:
                        await bot.send_photo(callback_query.from_user.id, photo)
                downloadVk.photo_url.clear()"""
                break
    except Exception as e:
        await bot.send_message(callback_query.from_user.id, text=f'Ошибка {e.args}')
