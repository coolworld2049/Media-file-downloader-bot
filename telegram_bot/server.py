import logging
import surrogates

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

from cloud_storage.YandexDisk import YandexDisk
from data import ConfigStorage
from social_nets.DownloadVk import DownloadVk
from states import States

# ---vk_api
downloadVk = DownloadVk()
config = ConfigStorage.configParser

# ---ya_disk_api
yandexDisk = YandexDisk()

# ---Bot
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = config["BOT_DATA"]["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)
MyStates = States.States
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# ---WEBHOOKS
HEROKU_APP_NAME = config.get("BOT_DATA", "HEROKU_APP_NAME")

WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = config.get("BOT_DATA", "WEBAPP_PORT")


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

    if downloadVk.user_authorized and yandexDisk.user_authorized:
        IK_continue_vk, msg = continue_action('continue_on_vk')
        await bot.send_message(message.from_user.id, text=msg, reply_markup=IK_continue_vk)


def continue_action(command: str):
    IK_continue_vk = ReplyKeyboardMarkup(one_time_keyboard=True,
                                         resize_keyboard=True).add(f'/{command}')
    msg = f'Теперь вы можете посмотреть что можно скачать из вашего аккаунта Vk.' \
          f' Нажмите /{command}'
    return IK_continue_vk, msg


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
    if downloadVk.user_authorized:
        album_list = downloadVk.display_albums()
        for a_id, title in album_list:
            IK_albums_list.add(InlineKeyboardButton(f'{title}', callback_data=str(a_id)))
        await bot.send_message(callback_query.from_user.id,
                               text='Список фотоальбомов, доступных для скачивания',
                               reply_markup=IK_albums_list)
    else:
        await bot.send_message(callback_query.from_user.id, text='Вы не авторизованы')


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
