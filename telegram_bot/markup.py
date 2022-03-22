from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from social_nets.vk_api.auth import scopes, user_authorized
from social_nets.vk_api.download_from_vk import display_albums

inline_keyboard_select_source = InlineKeyboardMarkup()

inline_buttonVk = InlineKeyboardButton('Vk', callback_data='buttonVk')
inline_buttonYt = InlineKeyboardButton('YouTube', callback_data='buttonYt')
inline_keyboard_select_source.add(inline_buttonVk, inline_buttonYt)


inline_keyboard_scopes_list = InlineKeyboardMarkup()

# display scopes list
scopes_str = scopes.split(',')
for scope in scopes_str:
    inline_keyboard_scopes_list.add(InlineKeyboardButton(f'{scope}', callback_data=f'{scope}'))


inline_keyboard_albums_list = InlineKeyboardMarkup()

# display albums list
if user_authorized:
    for album in display_albums():
        inline_keyboard_albums_list.add(InlineKeyboardButton(f'{album}', callback_data=f'{album}'))
