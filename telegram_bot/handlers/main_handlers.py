import surrogates
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from telegram_bot.core import MyStates, yandexDisk, downloadVk, bot, dp


def register_handlers_main(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_start, commands="start")
    dispatcher.register_message_handler(send_help, commands="help")
    dispatcher.register_message_handler(send_select, commands="select")

    dispatcher.register_callback_query_handler(callback_button_vk, lambda c: c.data == 'buttonVk')

    dispatcher.register_message_handler(message_auth_vk, state=MyStates.auth_vk)
    dispatcher.register_message_handler(message_auth_ya_disk, state=MyStates.auth_ya_disk)


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    await message.answer('Привет!\n\n'
                         'Это бот для загрузки ваших  медиафайлов из социальных сетей.\n\n'
                         'Сейчас доступна загрузка из Vk, YouTube\n\n'
                         'Список команд:\n'
                         '\t/select - выбрать соц. сеть\n'
                         '\t/help - список команд')
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("help", "Вывести справку"),
            types.BotCommand("select", "Выбрать соц сеть для загрузки")
        ])


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.answer('/select - выбрать соц. сеть\n'
                         '/help - список команд')


@dp.message_handler(commands=['select'])
async def send_select(message: types.Message):
    # display source list
    IK_select_source = InlineKeyboardMarkup()
    IK_select_source.add(InlineKeyboardButton(text=surrogates.decode('\ud83e\udde0') + 'Vk', callback_data='buttonVk'),
                         InlineKeyboardButton('YouTube', callback_data='buttonYt'))
    await bot.send_message(message.from_user.id, text='Выберите соц. сеть',
                           reply_markup=IK_select_source)


@dp.callback_query_handler(lambda c: c.data == 'buttonVk')
async def callback_button_vk(callback_query: types.CallbackQuery):
    if not downloadVk.user_authorized:
        IK_button_vk = InlineKeyboardMarkup()
        IK_button_vk.add(InlineKeyboardButton('Авторизация', url=downloadVk.send_auth_link()))
        await bot.send_message(callback_query.from_user.id,
                               text=f'Для загрузки данных из вашего аккаунта требуется авторизация'
                                    f' Нажмите на кнопку и скопируйте АДРЕС из адресной'
                                    f' строки в открывшемся окне браузера в чат:',
                               reply_markup=IK_button_vk)
        await MyStates.auth_vk.set()  # start FSM machine. state: waiting for user message
    else:
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
    if not downloadVk.user_authorized:
        async with state.proxy() as data:  # set the wait state
            data['auth_vk'] = message.text
            vk_auth_msg = downloadVk.auth_vk(data['auth_vk'])  # auth
            await bot.send_message(message.from_user.id, vk_auth_msg)  # auth result

        # actions after vk authorization
        if downloadVk.user_authorized:

            # send a link to the user for auth in yandex disk
            msg, IK_ya_auth = auth_ya_disk()
            await bot.send_message(message.from_user.id, text=msg, reply_markup=IK_ya_auth)

            await state.finish()
            await MyStates.auth_ya_disk.set()  # start FSM machine. state: waiting for user message
        else:
            await MyStates.auth_vk.set()
    else:
        await bot.send_message(message.from_user.id, text='Вы уже авторизовались в Vk!')
        await MyStates.select_vk_scope.set()


def auth_ya_disk():
    IK_ya_auth = InlineKeyboardMarkup()
    IK_ya_auth.add(InlineKeyboardButton('Yandex Disk', url=yandexDisk.auth_ya_disk_send_link()))
    msg = 'Данные будут загружены в отдельную папку' \
          ' в вашем облачном хранилище Yandex Disk.' \
          ' Для авторизации нажмите на кнопку и скопируйте ТОКЕН' \
          ' из адресной строки в открывшемся окне браузера в чат'
    return msg, IK_ya_auth


@dp.message_handler(state=MyStates.auth_ya_disk)
async def message_auth_ya_disk(message: types.Message, state: FSMContext):
    if not yandexDisk.user_authorized:
        async with state.proxy() as data:  # set the wait state
            data['token_ya_disk'] = message.text
            ya_auth_msg = yandexDisk.auth_ya_disk(data['token_ya_disk'])  # auth
        await bot.send_message(message.from_user.id, ya_auth_msg)  # auth result
        await state.finish()

        # actions after vk and ya disk authorization
        if downloadVk.user_authorized and yandexDisk.user_authorized:
            RK_goto_select_album = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            RK_goto_select_album.add(KeyboardButton('Перейти к выбору области загрузки'))
            await bot.send_message(message.from_user.id,
                                   text=f'Теперь вы можете посмотреть что можно'
                                        f' скачать из вашего аккаунта.',
                                   reply_markup=RK_goto_select_album)
            await MyStates.select_vk_scope.set()  # go to downloading from vk

        elif not yandexDisk.user_authorized:
            await MyStates.auth_ya_disk.set()
    else:
        await bot.send_message(message.from_user.id, text=f'Вы уже авторизовались в Yandex Disk!')


def continue_action(command: str, social_net_name: str):
    IK_continue_vk = ReplyKeyboardMarkup(one_time_keyboard=True,
                                         resize_keyboard=True).add(f'/{command}')
    msg = f'Теперь вы можете посмотреть что можно скачать из вашего аккаунта {social_net_name}.' \
          f' Нажмите /{command}'
    return IK_continue_vk, msg

# --> vk_handlers.py
