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
        scopes_str = downloadVk.scopes.split(',')
        for scope in scopes_str:
            IK_scopes_list.add(InlineKeyboardButton(scope, callback_data=scope))

        await bot.send_message(message.from_user.id, 'Выберите что необходимо скачать',
                               reply_markup=IK_scopes_list)


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
        data['callback_selected_album_id'] = callback_query.data
        callback_selected_album_id = int(data['callback_selected_album_id'])
    await state.finish()

    items = downloadVk.display_albums_id()
    for item in items:
        if item == callback_selected_album_id:
            await bot.send_message(callback_query.from_user.id, text=f'Загрузка альбома')
            downloadVk.save_photo_by_id(callback_selected_album_id)

            if downloadVk.photo_upload_completed:
                await bot.send_message(callback_query.from_user.id, text='Альбом загружен')

                RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                RK_goto_select_album.add(KeyboardButton('Перейти к выбору области загрузки'))
                await bot.send_message(callback_query.from_user.id, text='.',
                                       reply_markup=RK_goto_select_album)
                await MyStates.select_vk_scope.set()

            elif callback_query.data == 'back':
                await MyStates.select_vk_scope.set()

            else:
                await bot.send_message(callback_query.from_user.id, text='При загрузке альбома возникла ошибка')
                await MyStates.save_album
            break

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
    if downloadVk.docs_upload_completed:
        await bot.send_message(callback_query.from_user.id, text=f'Документы загружены')
        await MyStates.select_vk_scope.set()
    else:
        await MyStates.select_vk_scope.set()
