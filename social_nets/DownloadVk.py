import json
import os
import random
import time

import requests
from virtualenv.util.path import Path
from tqdm import tqdm

from data import ConfigStorage


class DownloadVk:
    def __init__(self):
        self.vk_app_id = 8109852
        self.scopes = "photos,video,notes,docs"
        self.user_authorized = False
        self.photo_url_list = []
        self.loading_complete = False
        self.config = ConfigStorage.configParser

    # authorization in user account

    def send_auth_link(self):
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={self.vk_app_id}&display=page&" \
                     f"redirect_uri=https://oauth.vk.com/blank.html" \
                     f".com/blank.html&scope={self.scopes}&response_type=token&v=5.131"

        return oAuth_link

    def auth_vk(self, vk_response_url: str):
        try:
            split_url = vk_response_url.split('#').copy()
            split_var = split_url[1].split('&')
            if split_url[0] == 'https://oauth.vk.com/blank.html':
                access_token = split_var[0].split('=')[-1:]
                expires_in = split_var[1].split('=')[-1:]
                user_id = split_var[2].split('=')[-1:]

                self.config.set("VK_ACC_DATA", "vk_token", access_token[0])
                self.config.set("VK_ACC_DATA", "vk_token_expires_in", expires_in[0])
                self.config.set("VK_ACC_DATA", "vk_user_id", user_id[0])
                self.config.write(open("config.ini", "w"))
                self.user_authorized = True
                return "Вы авторизованы в Vk!"
        except Exception as e:
            self.user_authorized = False
            return f"Ошибка авторизации!{e.args}"

    # get available scopes

    def get_scopes(self):
        try:
            if self.user_authorized:
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
        except Exception as e:
            return e.args

    # get JSON file with PHOTOS data

    def get_photos_by_id(self, photo_id):
        if self.user_authorized:
            self.config.read('config.ini')
            api = requests.get("https://api.vk.com/method/photos.getById", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'photos': str(self.config['VK_ACC_DATA']['vk_user_id'] + "_" + str(photo_id)),
                'v': 5.131
            })
            return api.json()

    def get_albums(self):
        if self.user_authorized:
            self.config.read('config.ini')
            api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'v': 5.131
            })
            return json.loads(api.text)

    def get_albums_count(self):
        if self.user_authorized:
            self.config.read('config.ini')
            api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'user_id': self.config['VK_ACC_DATA']['user_id'],
                'v': 5.131
            })
            return json.loads(api.text)

    def get_all_photos(self, offset=0, count=0):
        if self.user_authorized:
            self.config.read('config.ini')
            api = requests.get("https://api.vk.com/method/photos.getAll", params={
                'owner_id': int(self.config['VK_ACC_DATA']['vk_user_id']),
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'offset': offset,
                'count': count,
                'photo_sizes': 0,
                'v': 5.131
            })
            return json.loads(api.text)

    # get json file with DOCS data

    def get_docs(self, count=0):
        if self.user_authorized:
            self.config.read('config.ini')
            api = requests.get("https://api.vk.com/method/docs.get", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'count': count,
                'v': 5.131
            })
            return json.loads(api.text)

    # sorting all PHOTOS by albums_id and photo_id

    def albums_with_photos(self):
        try:
            if self.user_authorized:
                # get album id and photo id - getAll
                data = self.get_all_photos()
                album_id_photo_id = []
                count = 200
                i = 0
                while i <= data["response"]["count"]:
                    data = self.get_all_photos(offset=i, count=count)
                    for item in data["response"]["items"]:
                        album_id_photo_id.append([item["album_id"], item["id"]])
                    i += 200
                return album_id_photo_id
        except Exception as e:
            return e.args

    def display_albums(self):
        try:
            if self.user_authorized:
                json_data = self.get_albums()
                albums_id_title = []
                for albums in json_data["response"]["items"]:
                    albums_id_title.append([albums["id"], albums["title"]])
                return albums_id_title
        except Exception as e:
            return e.args

    def display_albums_title(self, album_id: int):
        try:
            if self.user_authorized:
                json_data = self.get_albums()
                albums_title = []
                for albums in json_data["response"]["items"]:
                    albums_title.append([albums["id"], albums["title"]])
                for i in range(len(albums_title)):
                    if albums_title[i][0] == album_id:
                        return str(albums_title[0][i])
        except Exception as e:
            return e.args

    def display_albums_id(self):
        try:
            if self.user_authorized:
                json_data = self.get_albums()
                albums_id = []
                for albums in json_data["response"]["items"]:
                    albums_id.append(albums["id"])
                return albums_id
        except Exception as e:
            return e.args

    # downloading PHOTOS by album

    def save_photo_by_id(self, selected_album_id: int):
        # 100 photo per 1 min
        if self.user_authorized:
            try:
                Path(os.curdir + "/Saved photos").mkdir(parents=True, exist_ok=True, mode=0o666)
                albums_with_photos_list = self.albums_with_photos()
                ownerAndPhotoId_list = []

                # id list with selected album photos
                for i in range(len(albums_with_photos_list)):
                    if albums_with_photos_list[i][0] == selected_album_id:
                        ownerAndPhotoId_list.append(albums_with_photos_list[i][1])

                for _ in tqdm(range(len(ownerAndPhotoId_list))):
                    for i in range(len(albums_with_photos_list)):
                        if albums_with_photos_list[i][0] == selected_album_id:
                            try:
                                ownerAndPhotoId = self.get_photos_by_id(albums_with_photos_list[i][1])
                                time.sleep(0.1)
                                self.photo_url_list = ownerAndPhotoId['response'][0]['sizes'][-1]['url']

                                """self.photo_url.append(photo_url_list)
                                print(photo_url_list)
                                vk_api = requests.get(photo_url_list)
                                album_title = self.display_albums_title(selected_album_id)
                                filename = album_title + str(random.randint(1153, 546864))
                                with open(f"C:/Users/R/PycharmProjects/Social-media-file-downloader/Saved photos/"
                                          f"{filename}.jpg", "wb") as save_image:
                                    save_image.write(vk_api.content)"""
                            except requests.exceptions.RequestException:
                                time.sleep(0.5)
                                continue
                        else:
                            continue
                    self.loading_complete = True

            except Exception as e:
                return e.args

    # downloading DOCS

    def save_docs(self):
        if self.user_authorized:
            Path(os.curdir + "/Saved docs").mkdir(parents=True, exist_ok=True, mode=0o666)
            data = self.get_docs()
            count = 100
            items_count = data["response"]["count"]
            i = 0
            while i <= data["response"]["count"]:
                if i != 0:
                    data = self.get_docs(count=count)

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
