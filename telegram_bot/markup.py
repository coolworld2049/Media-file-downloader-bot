from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from social_nets.vk_api.auth import scopes

inline_buttonVk = InlineKeyboardButton('Vk', callback_data='buttonVk')
inline_buttonYt = InlineKeyboardButton('YouTube', callback_data='buttonYt')
inline_keyboard = InlineKeyboardMarkup().add(inline_buttonVk, inline_buttonYt)


albums_dict = {'album1': '123', 'album2': '457', 'album3': '787'}
inline_keyboard_album_list = InlineKeyboardMarkup()
for key, value in albums_dict.items():
    inline_keyboard_album_list.add(InlineKeyboardButton(f'{key}', callback_data=f'{value}'))


scopes_str = scopes.split(',')
inline_keyboard_scopes_list = InlineKeyboardMarkup()
for value in scopes_str:
    inline_keyboard_scopes_list.add(InlineKeyboardButton(f'{value}', callback_data=f'{value}'))
