import emoji
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from telegram_bot.core import dp, downloadVk, bot, yandexDisk, MyStates


def register_handlers_vk(dispatcher: Dispatcher):
    dispatcher.register_message_handler(message_select_vk_scope, state=MyStates.select_vk_scope)
    dispatcher.register_callback_query_handler(callback_display_albums_list, lambda c: c.data == 'photos')
    dispatcher.register_callback_query_handler(callback_save_all_photo, state=MyStates.save_all_photo)
    dispatcher.register_callback_query_handler(callback_save_album, state=MyStates.save_album)
    dispatcher.register_callback_query_handler(callback_save_docs, lambda c: c.data == 'docs')


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
async def callback_display_albums_list(callback_query: types.CallbackQuery):
    album_list = downloadVk.display_albums(albums_data=False, albums_size=True)
    for album in album_list:
        for a_id, title, size, thumbnail in album:
            IK_albums_list = InlineKeyboardMarkup()
            IK_albums_list.add(InlineKeyboardButton(callback_data=str(a_id), text="скачать"))
            thumb = downloadVk.get_photo_by_id([thumbnail])['response'][0]['sizes'][2]['url']
            await bot.send_photo(callback_query.from_user.id, thumb,
                                 caption='Альбом: ' + title + f'. Размер: {size}',
                                 reply_markup=IK_albums_list)

    IK_actions = InlineKeyboardMarkup()
    IK_actions.add(InlineKeyboardButton(text=emoji.emojize(':star:') + ' Скачать все альбомы',
                                        callback_data='save_all_photo'))
    IK_actions.add(InlineKeyboardButton(text=emoji.emojize(':left_arrow:') + ' Назад',
                                        callback_data='back'))
    await bot.send_message(callback_query.from_user.id,
                           text=f'Также можно скачать все фотографии с аккаунта',
                           reply_markup=IK_actions)

    await MyStates.save_album.set()


@dp.callback_query_handler(state=MyStates.save_all_photo)  # TODO установить tqdm
async def callback_save_all_photo(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await bot.send_message(callback_query.from_user.id, text='Загрузка всех фотографий из VK')
    downloadVk.save_all_photo()

    if downloadVk.photo_download_completed:
        # uploading photo to Yandex Disk
        await bot.send_message(callback_query.from_user.id,
                               text=f'Загрузка фотографий в облачное хранилище')
        upload_result = yandexDisk.upload_file(url_list=downloadVk.all_photo_url_list,
                                               folder_name='All photo',
                                               extension='jpg',
                                               is_exist_extension=True,
                                               overwrite=False)
        downloadVk.all_photo_url_list.clear()

        if yandexDisk.upload_completed:
            await bot.send_message(callback_query.from_user.id, text=upload_result)
            url_for_download = yandexDisk.download_file(downloadVk.curr_album_title)
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Ссылка для загрузки файлов:\n'
                                        f'{url_for_download}')
            await MyStates.select_vk_scope.set()
        else:
            await bot.send_message(callback_query.from_user.id,
                                   text='При загрузке альбома на облако возникла ошибка.'
                                        ' Попробуйте снова')
            await MyStates.select_vk_scope.set()


@dp.callback_query_handler(state=MyStates.save_album)
async def callback_save_album(callback_query: types.CallbackQuery, state: FSMContext):
    downloadVk.bot_chat_id = callback_query.from_user.id
    yandexDisk.bot_chat_id = callback_query.from_user.id

    async with state.proxy() as data:
        if callback_query.data.isdigit():
            data['callback_data'] = callback_query.data
            callback_selected_album_id = int(data['callback_data'])
            await state.finish()

            await bot.send_message(callback_query.from_user.id, text=f'Загрузка альбома из VK')

            downloadVk.save_album_by_id(callback_selected_album_id)

            if downloadVk.photo_download_completed and (len(downloadVk.photo_url_list) > 0):

                # uploading photo to Yandex Disk
                await bot.send_message(callback_query.from_user.id,
                                       text=f'Загрузка альбома в облачное хранилище')

                downloadVk.curr_album_title = downloadVk.display_albums_title(callback_selected_album_id)
                yandexDisk.upload_file(url_list=downloadVk.photo_url_list,
                                       folder_name=downloadVk.curr_album_title,
                                       extension='jpg',
                                       is_exist_extension=True,
                                       overwrite=False)

                if yandexDisk.upload_completed and (len(yandexDisk.check_url_list) > 0):
                    await bot.send_message(callback_query.from_user.id,
                                           text=f'Загрузка альбома в облачное хранилище:\n'
                                                f'Path "{yandexDisk.subfolder_path}]"'
                                                f'Size {yandexDisk.count_uploaded_files}')

                    """downloadVk.save_files_locally()
                    with open(f"Saved photos/{downloadVk.curr_album_title}" + ".jpg", "wb") as read_file:
                        inputFile = InputFile(path_or_bytesio=f"Saved photos/{downloadVk.curr_album_title}",
                                              filename='photos')
                        await bot.send_document()"""

                    url_for_download = yandexDisk.download_file(downloadVk.curr_album_title)
                    await bot.send_message(callback_query.from_user.id,
                                           text=f'Ссылка для загрузки файлов:\n'
                                                f'{url_for_download}')

                    await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                                           reply_markup=goto_select_vk_scope())
                    await MyStates.select_vk_scope.set()
                else:
                    await bot.send_message(callback_query.from_user.id,
                                           text='При загрузке альбома на облако возникла ошибка.'
                                                ' Попробуйте снова')
                    await MyStates.save_album.set()
            else:
                await bot.send_message(callback_query.from_user.id,
                                       text='При загрузке альбома из VK возникла ошибка.'
                                            ' Попробуйте снова')
                await MyStates.save_album.set()

            downloadVk.photo_url_list.clear()

        elif callback_query.data == 'save_all_photo':
            await MyStates.save_all_photo.set()
            await callback_save_all_photo(callback_query, state)

        else:
            await bot.send_message(callback_query.from_user.id, text='Назад',
                                   reply_markup=goto_select_vk_scope())
            await MyStates.select_vk_scope.set()


@dp.callback_query_handler(lambda c: c.data == 'docs')
async def callback_save_docs(callback_query: types.CallbackQuery):
    downloadVk.bot_chat_id = callback_query.from_user.id
    yandexDisk.bot_chat_id = callback_query.from_user.id

    await bot.send_message(callback_query.from_user.id, text=f'Загрузка документов из VK')
    downloadVk.save_docs()

    if downloadVk.docs_download_completed:
        await bot.send_message(callback_query.from_user.id,
                               text=f'Загрузка документов в облачное хранилище')
        yandexDisk.upload_file(url_list=downloadVk.docs_url_ext_list,
                               folder_name=downloadVk.docs_folder_name,
                               is_exist_extension=False,
                               overwrite=False)
        if yandexDisk.upload_completed:
            url_for_download = yandexDisk.download_file(downloadVk.docs_folder_name)
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Ссылка для загрузки файлов:\n'
                                        f'{url_for_download}')
            await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                                   reply_markup=goto_select_vk_scope())
            await MyStates.select_vk_scope.set()
    else:
        await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                               reply_markup=goto_select_vk_scope())
        await MyStates.select_vk_scope.set()
