import configparser
import json
import os
import random
import time
import webbrowser

import pyautogui
import pyperclip
import requests
from virtualenv.util.path import Path


class DownloadVk:
    def __init__(self):
        self.vk_app_id = 8109852
        self.scopes = "friends,photos,video,notes,wall,docs"
        self.user_authorized = False
        self.config = configparser.ConfigParser()

    # storage file
    def storage_files(self):
        self.config.read('config.ini')
        self.config['VK_ACC_DATA'] = {'vk_app_id': self.vk_app_id,
                                      'vk_token': '',
                                      'token_expires_in': '',
                                      'vk_user_id': ''}
        self.config.write(open("config.ini", "w"))

        Path(os.curdir + "/Saved photos").mkdir(parents=True, exist_ok=True, mode=0o666)
        Path(os.curdir + "/Saved docs").mkdir(parents=True, exist_ok=True, mode=0o666)

    def auth_user(self):
        self.config.read('config.ini')

        try:
            oAuth_link = f"https://oauth.vk.com/authorize?client_id={self.vk_app_id}&display=page&redirect_uri=https://oauth.vk.com/blank.html" \
                         f".com/blank.html&scope={self.scopes}&response_type=token&v=5.131"
            webbrowser.open_new_tab(oAuth_link)

            pyautogui.click(0, 200)  # a random click for focusing the browser
            pyautogui.press('f6')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            vk_response_url: str = pyperclip.paste()  # for copying the selected url

            split_url = vk_response_url.split('#').copy()
            split_var = split_url[1].split('&')

            access_token = split_var[0].split('=')[-1:]
            expires_in = split_var[1].split('=')[-1:]
            user_id = split_var[2].split('=')[-1:]

            self.config.set("VK_ACC_DATA", "vk_token", access_token[0])
            self.config.set("VK_ACC_DATA", "token_expires_in", expires_in[0])
            self.config.set("VK_ACC_DATA", "vk_user_id", user_id[0])
            self.config.write(open("config.ini", "w"))
            self.user_authorized = True
            return 'Вы авторизованы'

        except Exception as e:
            self.user_authorized = False
            return f'Ошибка авторизации{e.args}'

    # return json file
    def get_scopes(self):
        scopes_list = []
        self.config.read('config.ini')

        api = requests.get("https://api.vk.com/method/apps.getScopes", params={
            'access_token': self.config['VK_ACC_DATA']['vk_token'],
            'owner_id': 'user',
            'v': 5.131
        })
        data = json.loads(api.text)
        i = 0
        while i <= data["response"]["count"]:
            for names in data["response"]["items"]:
                scopes_list.append(names["items"]["name"])
                scopes_list.append(',')
                i += 1
        return scopes_list

    def get_photos_by_id(self, photo_id):
        self.config.read('config.ini')

        api = requests.get("https://api.vk.com/method/photos.getById", params={
            'access_token': self.config['VK_ACC_DATA']['vk_token'],
            'photos': self.config['VK_ACC_DATA']['user_id'] + "_" + photo_id,
            'v': 5.131
        })
        return json.loads(api.text)

    def get_albums(self):
        self.config.read('config.ini')

        api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
            'access_token': self.config['VK_ACC_DATA']['vk_token'],
            'v': 5.131
        })
        return json.loads(api.text)

    def get_all_photos(self, offset=0, count=0):
        self.config.read('config.ini')

        api = requests.get("https://api.vk.com/method/photos.getAll", params={
            'owner_id': int(self.config['VK_ACC_DATA']['vk_user_id']),
            'access_token': self.config['VK_ACC_DATA']['vk_token'],
            'offset': offset,
            'count_photos': count,
            'photo_sizes': 0,
            'v': 5.131
        })
        return json.loads(api.text)

    # file loading and saving
    def docs_get(self, count=0):
        self.config.read('config.ini')

        api = requests.get("https://api.vk.com/method/docs.get", params={
            'access_token': self.config['VK_ACC_DATA']['vk_token'],
            'count': count,
            'v': 5.131
        })
        return json.loads(api.text)

    def albums_with_photos(self):
        # получаем список id альбома и id фотографии - getAll
        photo = self.get_all_photos()
        album_and_photos = [[]]
        c = 0
        while c <= photo["response"]["count"]:
            for photos in photo["response"]["items"]:
                album_and_photos.append([[photos["album_id"], photos["id"]]])  # [[album_id],[photo_id]]
                c += 1
        return album_and_photos

    def display_albums(self):
        i = 0
        json_data = self.get_albums()
        albums_id_title = [[]]
        albums_id = []
        while i <= json_data["response"]["count"]:
            for albums in json_data["response"]["items"]:
                albums_id_title.append([albums["id"], albums["title"]])
                albums_id.append(albums["id"])
                i += 1
        return albums_id

    def save_by_id(self):
        albums_list = self.get_albums()
        album_id_list = []

        # получаем список id всех альбомов аккаунта - getAlbums
        v = 0
        while v <= albums_list["response"]["count"]:
            for albums in albums_list["response"]["items"]:
                album_id_list.append(albums["id"])  # [[album_id]]
                v += 1
        full_album = self.albums_with_photos()
        for i in range(len(full_album)):
            for j in range(len(full_album[i])):
                print(full_album[i][j])

    def save_photo(self):
        data = self.get_all_photos()
        count = 1
        items_count = data["response"]["count"]
        i = 0
        while i <= data["response"]["count"]:
            if i != 0:
                data = self.get_all_photos(offset=i, count=count)
            for photos in data["response"]["items"]:
                photo_url = photos["sizes"][-1]["url"]

                filename = random.randint(1153, 546864)
                try:
                    time.sleep(0.1)
                    api = requests.get(photo_url)
                    with open(f"Saved photos/{filename}" + ".jpg", "wb") as write_file:
                        write_file.write(api.content)
                    i += 1
                    print(f"{i}/{items_count}")
                except requests.exceptions:
                    time.sleep(0.5)
                    continue

    def save_docs(self):
        data = self.docs_get()
        count = 100
        items_count = data["response"]["count"]
        i = 0
        while i <= data["response"]["count"]:
            if i != 0:
                data = self.docs_get(count=count)

            for docs in data["response"]["items"]:
                docs_url = docs["url"]
                filename = random.randint(1153, 5468645)
                try:
                    time.sleep(0.1)
                    api = requests.get(docs_url)
                    with open(f"Saved docs/{filename}." + docs["ext"], "wb") as write_file:
                        write_file.write(api.content)
                    i += 1
                    print(f"{i}/{items_count}")
                except requests.exceptions:
                    print("Server connection")
                    time.sleep(0.5)
                    continue
