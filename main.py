import configparser
import os
import time

import win32api
import win32process
import win32con
import webbrowser

from download_photo import save_photo
from download_docs import save_docs
from pathlib import Path

# variables
vk_app_id = 8090088

# storage conf data
config = configparser.ConfigParser()
config.read('config.ini')
config['VK_ACC_DATA'] = {'vk_app_id': vk_app_id,
                         'vk_token': '',
                         'vk_user_id': ''}
config.write(open("config.ini", "w"))

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

        print("Enter your access_token(copy from the address bar in the window that opens):")
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={vk_app_id}&display=page&redirect_uri=https://oauth.vk.com/blank.html" \
                     f".com/blank.html&scope={scopes_str}&response_type=token&v=5.131"
        webbrowser.open_new_tab(oAuth_link)

        config.set("VK_ACC_DATA", "vk_token", input())
        config.write(open("config.ini", "w"))

        print("Choose what you want to download(№):"
              "\n1.photos",
              "\n2.docs")
        scope_type = int(input())

        if scope_type == 1:
            print("Enter your user_id: ")
            config.set("VK_ACC_DATA", "vk_user_id", input())
            config.write(open("config.ini", "w"))
            time.sleep(0.9)
            save_photo()

        if scope_type == 2:
            save_docs()

    except IOError:
        print(BaseException.args)


"""def download(func):
    try:
        print("Start download [Y/n]:")
        if input().__str__().__contains__("Y" or "y"):
            func()
            print("Downloading...")

        else:
            print("Exit")
    except BaseException.args:
        print(BaseException.args)"""

if __name__ == "__main__":
    start_prog()
