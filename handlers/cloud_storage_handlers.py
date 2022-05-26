from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from cloud_storage.YandexDisk import YandexDisk
from core import MyStates, users_db, dp, bot
from handlers.start_handler import message_start
from handlers.vk_handlers import goto_select_vk_scope, callback_auth_vk


def register_cloud_storage(dispatcher: Dispatcher):
    dispatcher.register_message_handler(callback_select_storage, state=MyStates.select_storage)
    dispatcher.register_callback_query_handler(callback_auth_ya_disk, lambda c: c.data == 'auth_ya_disk')
    dispatcher.register_message_handler(message_auth_ya_disk, state=MyStates.auth_ya_disk)


@dp.callback_query_handler(state=MyStates.select_storage)
async def callback_select_storage(callback_query: types.CallbackQuery, state: FSMContext):
    IK_select_storage = InlineKeyboardMarkup()
    IK_select_storage.add(
        InlineKeyboardButton('Яндекс Диск', callback_data='auth_ya_disk'),
        InlineKeyboardButton('Гугл Диск', callback_data='auth_g_drive'))
    await bot.send_message(callback_query.from_user.id,
                           text='Выберите место куда необходимо загрузить ваши файлы',
                           reply_markup=IK_select_storage)
    await state.finish()


async def set_select_vk_scope_state(input_type: types.CallbackQuery | types.Message):
    await bot.send_message(input_type.from_user.id, text=f'Вы уже авторизовались в Яндекс Диске!')
    await bot.send_message(input_type.from_user.id,
                           text='Перейти к выбору области загрузки',
                           reply_markup=goto_select_vk_scope())
    await MyStates.select_vk_scope.set()


async def set_upload_user_file_state(input_type: types.CallbackQuery | types.Message):
    await MyStates.upload_user_file.set()
    RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    RK_goto_select_album.add(KeyboardButton('Далее'))
    await bot.send_message(input_type.from_user.id,
                           text=f"Отправьте файлы, который необходимо загрузить в "
                                f"{users_db['user'].get(input_type.from_user.id).get('cloud_storage')}",
                           reply_markup=RK_goto_select_album)


@dp.callback_query_handler(lambda c: c.data == 'auth_ya_disk')
async def callback_auth_ya_disk(callback_query: types.CallbackQuery):
    users_db['user'].upsert(
        {
            "user_id": callback_query.from_user.id,
            "cloud_storage": 'Яндекс Диск'
        }, pk="user_id")
    if not users_db['user'].get(callback_query.from_user.id).get('ya_user_authorized'):
        IK_ya_auth = InlineKeyboardMarkup()
        IK_ya_auth.add(InlineKeyboardButton('Авторизация в Яндекс Диске', url=YandexDisk().link()))
        await bot.send_message(callback_query.from_user.id,
                               text='Данные будут загружены в отдельную папку'
                                    ' в вашем облачном хранилище Яндекс Диск.'
                                    ' Для авторизации нажмите на кнопку и перешлите'
                                    ' семизначный КОД ПОДТВЕРЖДЕНИЯ боту',
                               reply_markup=IK_ya_auth)
        await MyStates.auth_ya_disk.set()
    elif users_db[f"{callback_query.from_user.id}_calls"].get(0).get('call_from') == callback_auth_vk.__name__:
        await set_select_vk_scope_state(callback_query)


@dp.message_handler(state=MyStates.auth_ya_disk)
async def message_auth_ya_disk(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # set the wait state
        data['token_ya_disk'] = message.text
        ya_auth_msg = await YandexDisk().auth(message.from_user.id, data['token_ya_disk'])  # auth

        await bot.send_message(message.from_user.id, ya_auth_msg)  # auth result
        # actions after vk and ya disk authorization
        if users_db['user'].get(message.from_user.id).get('ya_user_authorized'):
            await bot.send_message(message.from_user.id,
                                   text=f'Теперь вы можете перейти к загрузке.',
                                   reply_markup=goto_select_vk_scope())
            users_db['user'].upsert(
                {
                    "user_id": message.from_user.id,
                    "auth_attempts": 3
                }, pk="user_id")
            if users_db[f"{message.from_user.id}_calls"].get(0).get('call_from') == callback_auth_vk.__name__:
                await MyStates.select_vk_scope.set()

        # more than 3 login attempts
        elif users_db['user'].get(message.from_user.id).get('auth_attempts') <= 0:
            await state.finish()
            await message_start(message)
        else:
            users_db['user'].upsert(
                {
                    "user_id": message.from_user.id,
                    "auth_attempts": users_db['user'].get(message.from_user.id).get('auth_attempts') - 1
                }, pk="user_id")
