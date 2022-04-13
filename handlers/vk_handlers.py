import emoji
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from cloud_storage.YandexDisk import YandexDisk
from core import dp, bot, MyStates
from db.database import users_db
from social_nets.DownloadVk import DownloadVk


def register_handlers_vk(dispatcher: Dispatcher):
    dispatcher.register_callback_query_handler(callback_button_vk, lambda c: c.data == 'buttonVk')
    dispatcher.register_message_handler(message_auth_vk, state=MyStates.auth_vk)

    dispatcher.register_callback_query_handler(callback_auth_ya_disk, lambda c: c.data == 'auth_ya_disk')
    dispatcher.register_message_handler(message_auth_ya_disk, state=MyStates.auth_ya_disk)

    dispatcher.register_message_handler(message_select_vk_scope, state=MyStates.select_vk_scope)
    dispatcher.register_callback_query_handler(callback_display_albums_list, lambda c: c.data == 'photos')
    # dispatcher.register_callback_query_handler(callback_save_all_photo, state=MyStates.save_all_photo)
    dispatcher.register_callback_query_handler(callback_save_album, state=MyStates.save_album)

    # dispatcher.register_callback_query_handler(callback_save_docs, lambda c: c.data == 'docs')


@dp.callback_query_handler(lambda c: c.data == 'buttonVk')
async def callback_button_vk(callback_query: types.CallbackQuery):
    if not users_db['user'].get(callback_query.from_user.id).get('vk_user_authorized'):
        IK_button_vk = InlineKeyboardMarkup()
        IK_button_vk.add(InlineKeyboardButton('Авторизация в VK', url=DownloadVk().send_auth_link()))
        await bot.send_message(callback_query.from_user.id,
                               text=f'Для загрузки данных из вашего аккаунта требуется авторизация'
                                    f' Нажмите на кнопку и скопируйте АДРЕС из адресной'
                                    f' строки в чат:',
                               reply_markup=IK_button_vk)
        await MyStates.auth_vk.set()  # start FSM machine. state: waiting for user message

    elif not DownloadVk().check_token(callback_query.from_user.id):
        IK_button_vk = InlineKeyboardMarkup()
        IK_button_vk.add(InlineKeyboardButton('Авторизация в VK', url=DownloadVk().send_auth_link()))
        await bot.send_message(callback_query.from_user.id,
                               text=f'Для загрузки данных из вашего аккаунта требуется авторизация'
                                    f' Нажмите на кнопку и скопируйте АДРЕС из адресной'
                                    f' строки в чат:',
                               reply_markup=IK_button_vk)
        await MyStates.auth_vk.set()

    elif DownloadVk().check_token(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, text='Вы уже авторизовались в Vk!')
        RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        RK_goto_select_album.add(KeyboardButton('Перейти к выбору области загрузки'))
        await bot.send_message(callback_query.from_user.id,
                               text=f'Теперь вы можете посмотреть что можно'
                                    f' скачать из вашего аккаунта.',
                               reply_markup=RK_goto_select_album)
        await MyStates.select_vk_scope.set()


@dp.message_handler(state=MyStates.auth_vk)
async def message_auth_vk(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # set the wait state
        data['auth_vk'] = message.text
        vk_auth_msg = await DownloadVk().auth_vk(message.from_user.id, data['auth_vk'])  # auth
        await bot.send_message(message.from_user.id, vk_auth_msg)  # auth result

        # actions after vk authorization
        if users_db['user'].get(message.from_user.id).get('vk_user_authorized') \
                and not users_db['user'].get(message.from_user.id).get('y_api_token'):
            await state.finish()
            # select storage place
            IK_select_storage = InlineKeyboardMarkup()
            IK_select_storage.add(
                InlineKeyboardButton('Yandex Disk', callback_data='auth_ya_disk'),
                InlineKeyboardButton('Google Disk', callback_data='auth_g_drive'))
            await bot.send_message(message.from_user.id, text='Выберите место куда необходимо загрузить'
                                                              ' ваши файлы',
                                   reply_markup=IK_select_storage)
        else:
            await MyStates.auth_vk.set()


@dp.callback_query_handler(lambda c: c.data == 'auth_ya_disk')
async def callback_auth_ya_disk(message: types.Message):
    if not users_db['user'].get(message.from_user.id).get('ya_user_authorized') \
            and DownloadVk().check_token(message.from_user.id):
        IK_ya_auth = InlineKeyboardMarkup()
        IK_ya_auth.add(InlineKeyboardButton('Авторизация в Yandex Disk', url=YandexDisk().send_link()))
        await bot.send_message(message.from_user.id,
                               text='Данные будут загружены в отдельную папку'
                                    ' в вашем облачном хранилище Yandex Disk.'
                                    ' Для авторизации нажмите на кнопку и скопируйте ТОКЕН'
                                    ' из адресной строки в открывшемся окне браузера в чат',
                               reply_markup=IK_ya_auth)
        await MyStates.auth_ya_disk.set()


@dp.message_handler(state=MyStates.auth_ya_disk)
async def message_auth_ya_disk(message: types.Message, state: FSMContext):
    if not users_db['user'].get(message.from_user.id).get('ya_user_authorized') \
            and DownloadVk().check_token(message.from_user.id):

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
        await bot.send_message(message.from_user.id, text=f'Вы уже авторизовались в Yandex Disk!')
        await state.finish()
        await MyStates.select_vk_scope.set()


"""def continue_action(command: str, social_net_name: str):
    IK_continue_vk = ReplyKeyboardMarkup(one_time_keyboard=True,
                                         resize_keyboard=True).add(f'/{command}')
    msg = f'Теперь вы можете посмотреть что можно скачать из вашего аккаунта {social_net_name}.' \
          f' Нажмите /{command}'
    return IK_continue_vk, msg"""


@dp.message_handler(state=MyStates.select_vk_scope)
async def message_select_vk_scope(message: types.Message, state: FSMContext):
    await state.finish()
    if DownloadVk().check_token(message.from_user.id):
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
    if DownloadVk().check_token(callback_query.from_user.id):
        # await DownloadVk().save_photo_id_album_id(callback_query.from_user.id)  # get all photos
        album_list = await DownloadVk().display_album_thumb(callback_query.from_user.id)
        for album in album_list:
            for a_id, title, size, thumbnail in album:
                IK_albums_list = InlineKeyboardMarkup()
                IK_albums_list.add(InlineKeyboardButton(callback_data=str(a_id), text="скачать"))
                await bot.send_photo(callback_query.from_user.id,
                                     await DownloadVk().get_thumb(callback_query.from_user.id,
                                                                  thumbnail),
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
    else:
        await bot.send_message(callback_query.from_user.id, 'Истекло время действия ключа доступа.'
                                                            ' Необходимо авторизоваться заново')
        await MyStates.auth_vk.set()


"""@dp.callback_query_handler(state=MyStates.save_all_photo)
async def callback_save_all_photo(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await bot.send_message(callback_query.from_user.id, text='Загрузка всех фотографий из VK')
    DownloadVk().save_all_photo(callback_query.from_user.id)

    if DownloadVk().vk_photo_download_completed:
        # uploading photo to Yandex Disk
        await bot.send_message(callback_query.from_user.id,
                               text=f'Загрузка фотографий в облачное хранилище')
        upload_result = YandexDisk().upload_file(url_list=DownloadVk().all_photo_url_list, folder_name='All photo',
                                               extension='jpg', is_extension=True, overwrite=False)
        DownloadVk().all_photo_url_list.clear()

        if YandexDisk().upload_completed:
            await bot.send_message(callback_query.from_user.id, text=upload_result)
            url_for_download = YandexDisk().get_link_file(DownloadVk().curr_album_title)
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Ссылка для загрузки файлов:\n'
                                        f'{url_for_download}')
            await MyStates.select_vk_scope.set()
        else:
            await bot.send_message(callback_query.from_user.id,
                                   text='При загрузке альбома на облако возникла ошибка.'
                                        ' Попробуйте снова')
            await MyStates.select_vk_scope.set()"""


@dp.callback_query_handler(state=MyStates.save_album)
async def callback_save_album(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if DownloadVk().check_token(user_id):
        async with state.proxy() as data:
            if callback_query.data.isdigit():
                data['callback_data'] = callback_query.data
                callback_selected_album_id = int(data['callback_data'])
                await state.finish()

                await bot.send_message(callback_query.from_user.id, text=f'Загрузка альбома из VK')
                # downloading
                await DownloadVk().save_album_by_id(user_id, callback_selected_album_id)

                if users_db['user'].get(user_id).get('vk_photo_download_completed'):
                    await bot.send_message(callback_query.from_user.id,
                                           text=f'Загрузка альбома в облачное хранилище')

                    curr_album_title = DownloadVk().display_albums_title(user_id, callback_selected_album_id)
                    photo_url_ext_list = []
                    for pk_id in range(users_db[f'{user_id}'].count):
                        photo_url_ext_list.append(
                            [
                                users_db[f'{user_id}'].get(pk_id).get('photo_url'),
                                users_db[f'{user_id}'].get(pk_id).get('photo_ext')
                            ])

                    # uploading
                    await YandexDisk().upload_file(user_id, url_list=photo_url_ext_list,
                                                   folder_name=curr_album_title)

                    if users_db['user'].get(callback_query.from_user.id).get('ya_upload_completed'):
                        await bot.send_message(callback_query.from_user.id,
                                               text=f'Альбом загружен в облачное хранилище:\n'
                                                    f'Path "{YandexDisk().main_folder}/{curr_album_title}"\n'
                                                    f'Size {users_db["user"].get(user_id).get("number_uploaded_file")}')

                        url_for_download = await YandexDisk().get_link_file(user_id, curr_album_title)
                        await bot.send_message(callback_query.from_user.id,
                                               text=f'Ссылка для загрузки файлов:\n {url_for_download}')

                        await bot.send_message(callback_query.from_user.id,
                                               text='Перейти к выбору области загрузки')
                        await MyStates.select_vk_scope.set()
                    else:
                        await bot.send_message(callback_query.from_user.id,
                                               text='При загрузке альбома на облако возникла ошибка.')
                        await MyStates.save_album.set()
                else:
                    await bot.send_message(callback_query.from_user.id,
                                           text='При загрузке альбома из VK возникла ошибка.')
                    await MyStates.save_album.set()

            elif callback_query.data == 'save_all_photo':
                await MyStates.save_all_photo.set()
                # await callback_save_all_photo(callback_query, state)

            elif callback_query.data == 'back':
                await bot.send_message(callback_query.from_user.id, text='Назад',
                                       reply_markup=goto_select_vk_scope())
                await MyStates.select_vk_scope.set()
    else:
        await bot.send_message(callback_query.from_user.id, 'Истекло время действия ключа доступа.'
                                                            ' Необходимо авторизоваться заново')
        await MyStates.auth_vk.set()


"""@dp.callback_query_handler(lambda c: c.data == 'docs')
async def callback_save_docs(callback_query: types.CallbackQuery):
    DownloadVk().bot_chat_id = callback_query.from_user.id
    YandexDisk().bot_chat_id = callback_query.from_user.id

    await bot.send_message(callback_query.from_user.id, text=f'Загрузка документов из VK')
    DownloadVk().save_docs(callback_query.from_user.id)

    if DownloadVk().vk_docs_download_completed:
        await bot.send_message(callback_query.from_user.id,
                               text=f'Загрузка документов в облачное хранилище')
        YandexDisk().upload_file(url_list=DownloadVk().docs_url_ext, folder_name=DownloadVk().docs_folder_name,
                               overwrite=False)
        if YandexDisk().upload_completed:
            url_for_download = YandexDisk().get_link_file(DownloadVk().docs_folder_name)
            await bot.send_message(callback_query.from_user.id,
                                   text=f'Ссылка для загрузки файлов:\n'
                                        f'{url_for_download}')
            await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                                   reply_markup=goto_select_vk_scope())
            await MyStates.select_vk_scope.set()
    else:
        await bot.send_message(callback_query.from_user.id, text='Перейти к выбору области загрузки',
                               reply_markup=goto_select_vk_scope())
        await MyStates.select_vk_scope.set()"""
