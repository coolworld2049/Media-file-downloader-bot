import os
import sys

from aiogram.utils import executor

from telegram_bot.server import dp
from pathlib import Path

# storage downloaded files
Path(os.curdir + "/Saved photos").mkdir(parents=True, exist_ok=True, mode=0o666)
Path(os.curdir + "/Saved docs").mkdir(parents=True, exist_ok=True, mode=0o666)


def start_telegram_bot():
    executor.start_polling(dp)


def signal_handler():
    print('You pressed Ctrl+C!')
    sys.exit(0)


if __name__ == "__main__":
    try:
        start_telegram_bot()

    except KeyboardInterrupt:
        signal_handler()
