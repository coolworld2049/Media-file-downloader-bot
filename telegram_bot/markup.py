from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

inline_buttonVk = InlineKeyboardButton('Vk', callback_data='buttonVk')
inline_buttonYt = InlineKeyboardButton('YouTube', callback_data='buttonYt')

inline_keyboard = InlineKeyboardMarkup().add(inline_buttonVk, inline_buttonYt)
