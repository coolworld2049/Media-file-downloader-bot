import emoji
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from telegram_bot.core import dp, downloadVk, bot, yandexDisk, MyStates


def register_handlers_vk(dispatcher: Dispatcher):
    dispatcher.register_message_handler(message_select_vk_scope, state=MyStates.select_vk_scope)
    dispatcher.register_callback_query_handler(callback_albums_list, lambda c: c.data == 'photos')
    dispatcher.register_callback_query_handler(callback_save_album, state=MyStates.save_album)
    dispatcher.register_callback_query_handler(callback_save_docs, state=MyStates.save_docs)


@dp.message_handler(state=MyStates.select_vk_scope)
async def message_select_vk_scope(message: types.Message, state: FSMContext):
    await state.finish()
    if downloadVk.user_authorized and yandexDisk.user_authorized:
        # display scopes list
        IK_scopes_list = InlineKeyboardMarkup()
        scopes_list = downloadVk.scopes.split(',')
        IK_scopes_list.add(InlineKeyboardButton(emoji.emojize(scopes_list[0] + ' :bridge_at_night:'),
                                                callback_data=scopes_list[0]))
        IK_scopes_list.add(InlineKeyboardButton(emoji.emojize(scopes_list[1] + ' :page_facing_up:'),
                                                callback_data=scopes_list[1]))

        await bot.send_message(message.from_user.id, 'Выберите что необходимо скачать',
                               reply_markup=IK_scopes_list)


def goto_select_vk_scope():
    RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    RK_goto_select_album.add(KeyboardButton('Перейти к выбору области загрузки'))
    return RK_goto_select_album


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_albums_list(callback_query: types.CallbackQuery):
    # display albums list
    IK_albums_list = InlineKeyboardMarkup()
    album_list = downloadVk.display_albums()
    for a_id, title in album_list:
        IK_albums_list.add(InlineKeyboardButton(title, callback_data=str(a_id)))
    IK_albums_list.add(InlineKeyboardButton(text='<< Назад', callback_data='back'))

    await bot.send_message(callback_query.from_user.id,
                           text='Список фотоальбомов, доступных для скачивания',
                           reply_markup=IK_albums_list)

    await MyStates.save_album.set()


@dp.callback_query_handler(state=MyStates.save_album)
async def callback_save_album(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if callback_query.data.isdigit():
            data['callback_selected_album_id'] = callback_query.data
            callback_selected_album_id = int(data['callback_selected_album_id'])
            await state.finish()

            items = downloadVk.display_albums_id()
            for item in items:
                if item == callback_selected_album_id:
                    await bot.send_message(callback_query.from_user.id, text=f'Загрузка альбома из VK')
                    downloadVk.save_photo_by_id(callback_selected_album_id)

                    if downloadVk.photo_download_completed:

                        # uploading photo to Yandex Disk
                        for photo in downloadVk.photo_url_list:
                            yandexDisk.create_folder('Saved photo')
                            path = f'.jpg'
                            upload_result = yandexDisk.\
                                upload_file(photo, f'Saved_photo/'
                                                   f'{downloadVk.display_albums_title(callback_selected_album_id)}', 'jpg')
                            await bot.send_message(callback_query.from_user.id, text='Загрузка альбома на облако',
                                                   reply_markup=goto_select_vk_scope())
                        await MyStates.select_vk_scope.set()
                    else:
                        await bot.send_message(callback_query.from_user.id, text='При загрузке альбома возникла ошибка')
                        await MyStates.save_album.set()
                    break
        else:
            await bot.send_message(callback_query.from_user.id, text='Назад',
                                   reply_markup=goto_select_vk_scope())
            await state.finish()
            await MyStates.select_vk_scope.set()

    """# отправка фото в чат max 8 items
    try:
        if downloadVk.photo_upload_completed:
            for photo in downloadVk.photo_url_list:
                await bot.send_photo(callback_query.from_user.id, photo)
        downloadVk.photo_url_list.clear()

    except Exception as e:
        await bot.send_message(callback_query.from_user.id,
                               text=f'Ошибка отправки фото в чат {e.args}')"""


@dp.callback_query_handler(lambda c: c.data == 'docs')
async def callback_save_docs(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, text=f'Загрузка документов')
    downloadVk.save_docs()
    if downloadVk.docs_download_completed:
        await bot.send_message(callback_query.from_user.id, text='Документы загружены',
                               reply_markup=goto_select_vk_scope())
        await MyStates.select_vk_scope.set()
    else:
        await MyStates.select_vk_scope.set()
