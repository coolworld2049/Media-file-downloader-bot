import surrogates
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

from telegram_bot.core import MyStates, yandexDisk, downloadVk, bot, dp


def register_handlers_main(dp: Dispatcher):
    dp.register_message_handler(send_start, commands="start")
    dp.register_message_handler(send_help, commands="help")
    dp.register_message_handler(send_select, commands="select")

    dp.register_callback_query_handler(callback_button_vk, lambda c: c.data == 'buttonVk')

    dp.register_message_handler(message_auth_vk, state=MyStates.callback_auth_link)
    dp.register_message_handler(message_auth_ya_disk, state=MyStates.auth_ya_disk)


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
    if not downloadVk.user_authorized and not yandexDisk.user_authorized:
        IK_button_vk = InlineKeyboardMarkup()
        IK_button_vk.add(InlineKeyboardButton('Авторизация', url=downloadVk.send_auth_link()))
        await bot.send_message(callback_query.from_user.id,
                               text=f'Для загрузки данных из вашего аккаунта требуется авторизация'
                                    f' Нажмите на кнопку и скопируйте АДРЕС из адресной'
                                    f' строки в открывшемся окне браузера в чат:',
                               reply_markup=IK_button_vk)
        await MyStates.callback_auth_link.set()  # start FSM machine. state: waiting for user message
    else:
        await bot.send_message(callback_query.from_user.id, text='Вы уже авторизовались!')


def auth_ya_disk():
    IK_ya_auth = InlineKeyboardMarkup()
    IK_ya_auth.add(InlineKeyboardButton('Yandex Disk', url=yandexDisk.auth_ya_disk_send_link(),
                                        callback_data='ya_disk'))
    msg = 'Данные будут загружены в отдельную папку' \
          ' в вашем облачном хранилище Yandex Disk.' \
          ' Для авторизации нажмите на кнопку и скопируйте ТОКЕН' \
          ' из адресной строки в открывшемся окне браузера в чат'
    return msg, IK_ya_auth


@dp.message_handler(state=MyStates.callback_auth_link)
async def message_auth_vk(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # set the wait state
        data['callback_auth_link'] = message.text
        vK_auth_msg = downloadVk.auth_vk(data['callback_auth_link'])  # auth
        await bot.send_message(message.from_user.id, vK_auth_msg)  # auth result

    # send a link to the user for auth in yandex disk
    msg, IK_ya_auth = auth_ya_disk()
    await bot.send_message(message.from_user.id, text=msg, reply_markup=IK_ya_auth)

    await state.finish()
    await MyStates.auth_ya_disk.set()  # start FSM machine. state: waiting for user message


@dp.message_handler(state=MyStates.auth_ya_disk)
async def message_auth_ya_disk(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # set the wait state
        data['token_ya_disk'] = message.text
        ya_auth_msg = yandexDisk.auth_ya_disk(data['token_ya_disk'])  # auth
    await bot.send_message(message.from_user.id, ya_auth_msg)  # auth result
    await state.finish()

    # actions after full authorization
    if downloadVk.user_authorized and yandexDisk.user_authorized:
        IK_continue_vk, msg = continue_action('continue_on_vk')
        await bot.send_message(message.from_user.id, text=msg, reply_markup=IK_continue_vk)


def continue_action(command: str):
    IK_continue_vk = ReplyKeyboardMarkup(one_time_keyboard=True,
                                         resize_keyboard=True).add(f'/{command}')
    msg = f'Теперь вы можете посмотреть что можно скачать из вашего аккаунта Vk.' \
          f' Нажмите /{command}'
    return IK_continue_vk, msg