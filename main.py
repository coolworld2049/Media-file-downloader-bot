import configparser
import os
import sys
import time

import win32api
import win32process
import win32con
import webbrowser

from aiogram.utils import executor

from telegram_api.server import dp
from vk_api.download_photo import save_photo
from vk_api.download_docs import save_docs
from pathlib import Path

# variables
vk_app_id = 8090088

# storage conf data
config = configparser.ConfigParser()
config.read('config.ini')
config['VK_ACC_DATA'] = {'vk_app_id': vk_app_id,
                         'vk_token': '',
                         'vk_user_id': ''}
config.write(open("config.ini", "w+"))

# storage downloaded files
Path(os.curdir + "/Saved photos").mkdir(parents=True, exist_ok=True, mode=0o666)
Path(os.curdir + "/Saved docs").mkdir(parents=True, exist_ok=True, mode=0o666)

# .py priority
pid = win32api.GetCurrentProcessId()
handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)


def start_prog():
    try:
        scopes_str = "photos,docs"
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={vk_app_id}&display=page&redirect_uri=https://oauth.vk.com/blank.html" \
                     f".com/blank.html&scope={scopes_str}&response_type=token&v=5.131"
        webbrowser.open_new_tab(oAuth_link)

        config.set("VK_ACC_DATA", "vk_token", input("Enter your access_token(copy from the address bar"
                                                    " in the window that opens):\n"))
        config.write(open("config.ini", "w"))

        print("\nChoose what you want to download(№):"
              "\n\t1.photos",
              "\n\t2.docs")
        scope_type = int(input())

        if scope_type == 1:
            while True:
                input_data = input("\nEnter your user_id:\n")
                if not input_data.isnumeric():
                    print("You didn't enter a number. Try again:")
                elif not 100000000 <= int(input_data) <= 999999999:
                    print("Your number is out of range. Try again")
                else:
                    break
            config.set("VK_ACC_DATA", "vk_user_id", input_data)
            config.write(open("config.ini", "w"))
            time.sleep(0.9)
            save_photo()  # def
            path_data_photo = os.path.abspath("Saved data/Saved docs")
            print(f"\nLoading is complete. The downloaded files are located at {path_data_photo}")

        if scope_type == 2:
            save_docs()  # def
            path_data_docs = os.path.abspath("Saved data/Saved docs")
            print(f"\nLoading is complete. The downloaded files are located at {path_data_docs}")

    except IOError:
        print(BaseException.args)


def start_telegram_bot():
    executor.start_polling(dp, skip_updates=True)


def signal_handler():
    print('You pressed Ctrl+C!')
    sys.exit(0)


if __name__ == "__main__":
    try:
        start_prog()
        # start_telegram_bot()
    except KeyboardInterrupt:
        signal_handler()
