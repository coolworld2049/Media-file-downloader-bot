import configparser
import os
import win32api
import win32process
import win32con
import webbrowser

from download_photo import save_photo
from download_docs import save_docs

# storage conf data
config = configparser.ConfigParser()
config.read('config.ini')
if os.path.isfile("config.ini"):
    config['VK_ACC_DATA'] = {'vk_app_id': 8090088,
                             'vk_token': '',
                             'vk_album_id': ''}

with open("config.ini", "w") as create_file:
    config.write(create_file)

# variables
vk_app_id = config['VK_ACC_DATA']['vk_app_id']
vk_token = config['VK_ACC_DATA']['vk_token']
vk_album_id = config['VK_ACC_DATA']['vk_album_id']

# .py priority
pid = win32api.GetCurrentProcessId()
handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)


def start_prog():
    try:
        scopes_str = "photos,docs"
        if len(vk_token) == 0:
            print("Enter your access_token(copy from the address bar in the window that opens):")
            oAuth_link = f"https://oauth.vk.com/authorize?client_id={vk_app_id}&display=page&redirect_uri=https://oauth.vk" \
                         f".com/blank.html&scope={scopes_str}&response_type=token&v=5.131"
            webbrowser.open_new_tab(oAuth_link)
            config.set("VK_ACC_DATA", "vk_token", input())
            config.write(open("config.ini", "w"))

        print("Choose what you want to download(№):"
              "1.photos",
              "2.docs")
        scope_type = int(input())

        if scope_type == 1:
            print("Enter your album id: ")
            config.set("VK_ACC_DATA", "vk_album_id", input())
            config.write(open("config.ini", "w"))
            download(save_photo())

        if scope_type == 2:
            download(save_docs())

    except IOError:
        print(BaseException.args)


def download(func):
    try:
        print("Start download [Y/n]:")
        dwn = input().__str__()

        if dwn.__contains__("Y" or "y"):
            func()
            print("...")

        else:
            print("Exit")
    except BaseException.args:
        print(BaseException.args)


def terminate_prog():
    if os.path.exists("config.ini"):
        os.remove("config.ini")


if __name__ == "__main__":
    start_prog()
    # terminate_prog()
