import configparser
import json
import random
import time
import win32api
import win32process
import win32con
import requests
import webbrowser

config = configparser.ConfigParser()
config.read('config.ini')

VK_APP_ID = config['VK_ACC_DATA']['VK_APP_ID']
VK_TOKEN = config['VK_ACC_DATA']['VK_TOKEN']
VK_ALBUM_ID = config['VK_ACC_DATA']['VK_ALBUM_ID']


def get_photo_data(offset=0, count=0):
    api = requests.get("https://api.vk.com/method/photos.getAll", params={
        'owner_id': VK_ALBUM_ID,
        'access_token': VK_TOKEN,
        'offset': offset,
        'count_photos': count,
        'photo_sizes': 0,
        'v': 5.131
    })

    with open("photos data", "w") as write_file:
        json.dump(json.loads(api.text)["response"], write_file, indent=4)

    return json.loads(api.text)


def download_photo():
    data = get_photo_data()
    count = 1
    i = 0
    while i <= data["response"]["count"]:
        if i != 0:
            data = get_photo_data(offset=i, count=count)

        for photos in data["response"]["items"]:
            photo_url = photos["sizes"][-1]["url"]
            filename = random.randint(1153, 546864)
            try:
                time.sleep(0.1)
                api = requests.get(photo_url)
                with open(f"Saved photo/{filename}" + ".jpg", "wb") as write_file:
                    write_file.write(api.content)
                i += 1
                print(i)
            except requests.exceptions:
                time.sleep(0.5)
                continue


def process_priority():
    pid = win32api.GetCurrentProcessId()
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)


def start():
    oAuth_link = f"https://oauth.vk.com/authorize?client_id={VK_APP_ID}&display=page&redirect_uri=https://oauth.vk" \
                 f".com/blank.html&scope=photos&response_type=token&v=5.131 "

    webbrowser.open_new_tab(oAuth_link)

    try:
        print("Enter your access_token: ")
        config.set("VK_ACC_DATA", "VK_TOKEN", input())
        config.write(open("config.ini", "w"))

        print("Enter your album id: ")
        config.set("VK_ACC_DATA", "VK_ALBUM_ID", input())
        config.write(open("config.ini", "w"))

    except IOError:
        print("IOError: Invalid data format")

    try:
        print("Start download [Y/n]:")
        dwn = input().__str__()

        if dwn.__contains__("Y" or "y"):
            download_photo()
            print()
        else:
            print("Exit")
    except BaseException.args:
        print(BaseException.args)


if __name__ == "__main__":
    process_priority()
    start()
