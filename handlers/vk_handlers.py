import emoji
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove

from cloud_storage.YandexDisk import YandexDisk
from core import dp, bot, MyStates, users_db
from social_nets.DownloadVk import DownloadVk


def register_handlers_vk(dispatcher: Dispatcher):
    dispatcher.register_callback_query_handler(callback_button_vk, lambda c: c.data == 'buttonVk')
    dispatcher.register_message_handler(message_auth_vk, state=MyStates.auth_vk)
    dispatcher.register_message_handler(callback_select_storage, state=MyStates.select_storage)
    dispatcher.register_callback_query_handler(callback_auth_ya_disk, lambda c: c.data == 'auth_ya_disk')
    dispatcher.register_message_handler(message_auth_ya_disk, state=MyStates.auth_ya_disk)
    dispatcher.register_message_handler(message_select_vk_scope, state=MyStates.select_vk_scope)
    dispatcher.register_callback_query_handler(callback_display_albums_list, lambda c: c.data == 'photos')
    dispatcher.register_callback_query_handler(callback_save_album, state=MyStates.save_album)
    dispatcher.register_callback_query_handler(callback_save_docs, lambda c: c.data == 'docs')


@dp.callback_query_handler(lambda c: c.data == 'buttonVk')
async def callback_button_vk(callback_query: types.CallbackQuery):
    if not users_db['user'].get(callback_query.from_user.id).get('vk_user_authorized') \
            or not await DownloadVk().check_token(callback_query.from_user.id):
        IK_button_vk = InlineKeyboardMarkup()
        IK_button_vk.add(InlineKeyboardButton('Авторизация в VK', url=DownloadVk().send_auth_link()))
        await bot.send_message(callback_query.from_user.id,
                               text=f'Для загрузки данных из вашего аккаунта требуется авторизация'
                                    f' Нажмите на кнопку и перешлите URL АДРЕС боту',
                               reply_markup=IK_button_vk)
        await MyStates.auth_vk.set()  # start FSM machine. state: waiting for user message
    else:
        RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        RK_goto_select_album.add(KeyboardButton('Далее'))
        await bot.send_message(callback_query.from_user.id, text=f'Вы авторизованы в VK!',
                               reply_markup=RK_goto_select_album)
        await MyStates.select_storage.set()


@dp.message_handler(state=MyStates.auth_vk)
async def message_auth_vk(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # set the wait state
        data['auth_vk'] = message.text
        vk_auth_msg = await DownloadVk().auth_vk(message.from_user.id, data['auth_vk'])  # auth
        await bot.send_message(message.from_user.id, vk_auth_msg)  # auth result

        # actions after vk authorization
        if users_db['user'].get(message.from_user.id).get('vk_user_authorized'):
            await state.finish()
            RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            RK_goto_select_album.add(KeyboardButton('Далее'))
            await bot.send_message(message.from_user.id, text=f'Далее',
                                   reply_markup=RK_goto_select_album)
            await MyStates.select_storage.set()
        else:
            await MyStates.auth_vk.set()


@dp.callback_query_handler(state=MyStates.select_storage)
async def callback_select_storage(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if users_db['user'].get(callback_query.from_user.id).get('vk_user_authorized'):
        IK_select_storage = InlineKeyboardMarkup()
        IK_select_storage.add(
            InlineKeyboardButton('Yandex Disk', callback_data='auth_ya_disk'),
            InlineKeyboardButton('Google Disk', callback_data='auth_g_drive'),
            InlineKeyboardButton('Uploadgram', callback_data='uploadgram'))

        await bot.send_message(callback_query.from_user.id,
                               text='Выберите место куда необходимо загрузить ваши файлы',
                               reply_markup=IK_select_storage)


@dp.callback_query_handler(lambda c: c.data == 'auth_ya_disk')
async def callback_auth_ya_disk(callback_query: types.CallbackQuery):
    if not users_db['user'].get(callback_query.from_user.id).get('ya_user_authorized'):
        IK_ya_auth = InlineKeyboardMarkup()
        IK_ya_auth.add(InlineKeyboardButton('Авторизация в Yandex Disk', url=YandexDisk().send_link()))
        await bot.send_message(callback_query.from_user.id,
                               text='Данные будут загружены в отдельную папку'
                                    ' в вашем облачном хранилище Yandex Disk.'
                                    ' Для авторизации нажмите на кнопку и перешлите'
                                    ' полученный КОД боту',
                               reply_markup=IK_ya_auth)
        await MyStates.auth_ya_disk.set()
    else:
        await bot.send_message(callback_query.from_user.id, text=f'Вы уже авторизовались в Yandex Disk!')
        await bot.send_message(callback_query.from_user.id,
                               text='Перейти к выбору области загрузки',
                               reply_markup=goto_select_vk_scope())
        await MyStates.select_vk_scope.set()


@dp.message_handler(state=MyStates.auth_ya_disk)
async def message_auth_ya_disk(message: types.Message, state: FSMContext):
    if not users_db['user'].get(message.from_user.id).get('ya_user_authorized'):
        async with state.proxy() as data:  # set the wait state
            data['token_ya_disk'] = message.text
        ya_auth_msg = await YandexDisk().auth(message.from_user.id, data['token_ya_disk'])  # auth
        await bot.send_message(message.from_user.id, ya_auth_msg)  # auth result

        # actions after vk and ya disk authorization
        if users_db['user'].get(message.from_user.id).get('ya_user_authorized') \
                and users_db['user'].get(message.from_user.id).get('ya_user_authorized'):
            await bot.send_message(message.from_user.id,
                                   text=f'Теперь вы можете посмотреть что можно'
                                        f' скачать из вашего аккаунта.',
                                   reply_markup=goto_select_vk_scope())
            await state.finish()
            await MyStates.select_vk_scope.set()  # go to downloading from vk
        else:
            await MyStates.auth_ya_disk.set()
    else:
        await state.finish()
        await bot.send_message(message.from_user.id, text=f'Вы уже авторизовались в Yandex Disk!')
        await bot.send_message(message.from_user.id,
                               text='Перейти к выбору области загрузки',
                               reply_markup=goto_select_vk_scope())
        await MyStates.select_vk_scope.set()


@dp.message_handler(state=MyStates.select_vk_scope)
async def message_select_vk_scope(message: types.Message, state: FSMContext):
    await state.finish()
    if await DownloadVk().check_token(message.from_user.id):
        # display scopes list
        IK_scopes_list = InlineKeyboardMarkup()
        scopes_list = DownloadVk().scopes.split(',')
        IK_scopes_list.add(InlineKeyboardButton(emoji.emojize(scopes_list[0] + ' :bridge_at_night:'),
                                                callback_data=scopes_list[0]))
        IK_scopes_list.add(InlineKeyboardButton(emoji.emojize(scopes_list[1] + ' :page_facing_up:'),
                                                callback_data=scopes_list[1]))
        await bot.send_message(message.from_user.id, 'Выберите что необходимо скачать',
                               reply_markup=IK_scopes_list)
    else:
        await bot.send_message(message.from_user.id, 'Истекло время действия ключа доступа.'
                                                     ' Необходимо авторизоваться заново')
        await MyStates.auth_vk.set()


def goto_select_vk_scope():
    RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    RK_goto_select_album.add(KeyboardButton('Перейти к выбору области загрузки'))
    return RK_goto_select_album


@dp.callback_query_handler(lambda c: c.data == 'photos')
async def callback_display_albums_list(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id,
                           text='Подождите пока бот получит все фотографии из аккаунта',
                           reply_markup=ReplyKeyboardRemove())
    await DownloadVk().upsert_all_photos_into_db(callback_query.from_user.id)
    album_params = await DownloadVk().display_album(callback_query.from_user.id)
    for a_id, title, size, thumbnail in album_params:
        IK_albums_list = InlineKeyboardMarkup()
        IK_albums_list.add(InlineKeyboardButton(callback_data=str(a_id), text="скачать"))
        thumb_url = await DownloadVk().get_photo_by_id(callback_query.from_user.id, thumbnail)
        await bot.send_photo(callback_query.from_user.id, thumb_url['response'][0]['sizes'][-1]['url'],
                             caption='Альбом: ' + title + f'. Размер: {size}',
                             reply_markup=IK_albums_list)

    IK_actions = InlineKeyboardMarkup()
    IK_actions.add(InlineKeyboardButton(text=emoji.emojize(':star:') + ' Скачать все альбомы',
                                        callback_data='save_all_photos'))
    IK_actions.add(InlineKeyboardButton(text=emoji.emojize(':left_arrow:') + ' Назад',
                                        callback_data='back'))
    await bot.send_message(callback_query.from_user.id,
                           text=f'Также можно скачать все фотографии с аккаунта',
                           reply_markup=IK_actions)
    await bot.send_message(callback_query.from_user.id,
                           text=f'Внимание! Повторяющиеся фотографии будут удалены из списка загрузки.'
                                f' Поэтому количество скачанных фотографий может отличаться от'
                                f' их количества в альбоме')
    await MyStates.save_album.set()


@dp.callback_query_handler(state=MyStates.save_album)
async def callback_save_album(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    async with state.proxy() as data:
        if callback_query.data.isdigit() or callback_query.data.startswith('-'):
            if not callback_query.data.startswith('-'):
                data['callback_data'] = callback_query.data
                callback_selected_album_id = int(data['callback_data'])
                await state.finish()
            else:
                data['callback_data'] = callback_query.data
                callback_selected_album_id = str(data['callback_data'])
                await state.finish()

            await bot.send_message(callback_query.from_user.id, text=f'Загрузка альбома из VK',
                                   reply_markup=ReplyKeyboardRemove())
            # downloading
            await DownloadVk().download_album_by_id(user_id, callback_selected_album_id)

            if users_db['user'].get(user_id).get('vk_photo_download_completed'):
                await bot.send_message(callback_query.from_user.id,
                                       text=f'Загрузка альбома в облачное хранилище')
                curr_album_title = await DownloadVk().display_albums_title(user_id, callback_selected_album_id)
                photo_url_ext = \
                    {
                        users_db[f'{user_id}_photos'].get(pk_id).get('photo_url'):
                            users_db[f'{user_id}_photos'].get(pk_id).get('photo_ext')
                        for pk_id in range(users_db[f'{user_id}_photos'].count)
                    }

                # uploading
                await YandexDisk().upload_file(user_id, data=photo_url_ext, folder_name=curr_album_title)

                if users_db['user'].get(callback_query.from_user.id).get('ya_upload_completed'):
                    url_for_download = await YandexDisk().publish(user_id, curr_album_title)
                    await bot.send_message(callback_query.from_user.id,
                                           text=url_for_download)

                    await bot.send_message(callback_query.from_user.id,
                                           text='Перейти к выбору области загрузки',
                                           reply_markup=goto_select_vk_scope())
                    await MyStates.select_vk_scope.set()
                else:
                    await bot.send_message(callback_query.from_user.id,
                                           text='При загрузке альбома на облако возникла ошибка.')
                    await MyStates.save_album.set()
            else:
                await bot.send_message(callback_query.from_user.id,
                                       text='При загрузке альбома из VK возникла ошибка.')
                await MyStates.save_album.set()

        elif callback_query.data == 'save_all_photos':
            await callback_save_all_photo(callback_query)
        elif callback_query.data == 'back':
            await bot.send_message(callback_query.from_user.id, text='Назад',
                                   reply_markup=goto_select_vk_scope())
            await MyStates.select_vk_scope.set()


async def callback_save_all_photo(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    limit = 7000
    albums = await DownloadVk().get_albums(user_id)
    count_photos = sum([alb['size'] for alb in albums['response']['items']])
    albums_ids = [item['id'] for item in albums['response']['items']]

    if count_photos <= limit:
        await bot.send_message(callback_query.from_user.id, text=f'Загрузка всех фото из VK',
                               reply_markup=ReplyKeyboardRemove())
        # download all photos
        await DownloadVk().download_album_by_id(user_id, albums_ids)

        if users_db['user'].get(user_id).get('vk_photo_download_completed'):
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Загрузка фото в облачное хранилище')
            photo_url_ext = \
                {
                    users_db[f'{user_id}_photos'].get(pk_id).get('photo_url'):
                        users_db[f'{user_id}_photos'].get(pk_id).get('photo_ext')
                    for pk_id in range(users_db[f'{user_id}_photos'].count)
                }
            # uploading all photos
            await YandexDisk().upload_file(user_id, data=photo_url_ext, folder_name="All photos")

            if users_db['user'].get(callback_query.from_user.id).get('ya_upload_completed'):
                url_for_download = await YandexDisk().publish(user_id, 'All photos')
                await bot.send_message(callback_query.from_user.id,
                                       text=url_for_download)
                await bot.send_message(callback_query.from_user.id,
                                       text='Перейти к выбору области загрузки',
                                       reply_markup=goto_select_vk_scope())
                await MyStates.select_vk_scope.set()
            else:
                await bot.send_message(callback_query.from_user.id,
                                       text='При загрузке фото на облако возникла ошибка.')
        else:
            await bot.send_message(callback_query.from_user.id,
                                   text='При загрузке фото из VK возникла ошибка.')
    else:
        await bot.send_message(callback_query.from_user.id,
                               text=f'Общее количество загружаемых фотографий'
                                    f' не может превышать {limit}')


@dp.callback_query_handler(lambda c: c.data == 'docs')
async def callback_save_docs(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.send_message(callback_query.from_user.id, text=f'Загрузка документов из VK')
    res = await DownloadVk().download_docs(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, text=res)
    if users_db['user'].get(user_id).get('vk_docs_download_completed'):
        await bot.send_message(callback_query.from_user.id,
                               text=f'Загрузка документов в облачное хранилище')
        docs_url_ext = \
            {
                users_db[f'{user_id}_docs'].get(pk_id).get('docs_url'):
                    users_db[f'{user_id}_docs'].get(pk_id).get('docs_ext')
                for pk_id in range(users_db[f'{user_id}_docs'].count)
            }
        await YandexDisk().upload_file(user_id, data=docs_url_ext, folder_name='docs')

        if users_db['user'].get(user_id).get('ya_upload_completed'):
            url_for_download = await YandexDisk().publish(user_id, 'docs')
            await bot.send_message(callback_query.from_user.id,
                                   text=url_for_download)
            await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                                   reply_markup=goto_select_vk_scope())
            await MyStates.select_vk_scope.set()
    else:
        await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                               reply_markup=goto_select_vk_scope())
        await MyStates.select_vk_scope.set()
