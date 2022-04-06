import json
import os
import time
from itertools import islice

import psutil
import requests
from tqdm.contrib.telegram import tqdm

from data import ConfigStorage


class DownloadVk:
    def __init__(self):
        self.vk_app_id: int = 8109852
        self.scopes: str = "photos,docs"
        self.user_authorized = False
        self.bot_chat_id = ''
        self.all_photo_url_list = []
        self.photo_url_list = []
        self.docs_url_ext_list = []
        self.photo_download_completed = False
        self.docs_download_completed = False
        self.photo_url_list_size_MB: float = 0.0
        self.album_folder_name = []
        self.curr_album_title = 'default'
        self.docs_folder_name = 'docs'
        self.config = ConfigStorage.configParser
        self.path_to_config = ConfigStorage.path

    # authorization in user account

    def send_auth_link(self):
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={self.vk_app_id}&display=page&" \
                     f"redirect_uri=https://oauth.vk.com/blank.html" \
                     f".com/blank.html&scope={self.scopes}&response_type=token&v=5.131"

        return oAuth_link

    def auth_vk(self, vk_response_url: str):
        self.config.read(self.path_to_config)

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
            else:
                return f"Ошибка авторизации в Vk!"
        except Exception as e:
            self.user_authorized = False
            return f"Ошибка авторизации в Vk! {e.args}"

    # get available scopes

    def get_scopes(self):
        self.config.read(self.path_to_config)

        try:
            if self.user_authorized:
                scopes_list = []
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

    def get_photo_by_id(self, photo_id: list):
        self.config.read(self.path_to_config)

        if self.user_authorized:
            id_list = ''
            user_id = str(self.config['VK_ACC_DATA']['vk_user_id'])
            for item in photo_id:
                id_list += ',' + user_id + '_' + str(item)

            api = requests.get("https://api.vk.com/method/photos.getById", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'photos': id_list,
                'v': 5.131
            })
            self.photo_url_list_size_MB += len(api.content) / 1048576
            return api.json()

    def get_albums(self):
        self.config.read(self.path_to_config)

        if self.user_authorized:
            api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'v': 5.131
            })
            return json.loads(api.text)

    def get_albums_count(self):
        self.config.read(self.path_to_config)

        if self.user_authorized:
            api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'user_id': self.config['VK_ACC_DATA']['user_id'],
                'v': 5.131
            })
            return json.loads(api.text)

    def get_all_photos(self, offset=0, count=0):
        self.config.read(self.path_to_config)

        if self.user_authorized:
            api = requests.get("https://api.vk.com/method/photos.getAll", params={
                'owner_id': int(self.config['VK_ACC_DATA']['vk_user_id']),
                'access_token': self.config['VK_ACC_DATA']['vk_token'],
                'offset': offset,
                'count': count,
                'photo_sizes': 1,
                'v': 5.131
            })
            return json.loads(api.text)

    # get json file with DOCS data

    def get_docs(self, count=0):
        """MAX count = 200"""
        self.config.read(self.path_to_config)

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

    def display_albums(self, albums_data=True, albums_size=False):
        try:
            if self.user_authorized and albums_data and not albums_size:
                json_data = self.get_albums()
                albums_id_title = []
                for albums in json_data["response"]["items"]:
                    albums_id_title.append([albums["id"], albums["title"]])
                return albums_id_title

            if self.user_authorized and albums_size:
                json_data = self.get_albums()
                albums_id_title_size_thumb = []
                for albums in json_data["response"]["items"]:
                    albums_id_title_size_thumb.append([[albums["id"],
                                                        albums["title"],
                                                        albums["size"],
                                                        albums["thumb_id"]]])
                return albums_id_title_size_thumb

        except Exception as e:
            return e.args

    def display_albums_title(self, album_id: int):
        try:
            if self.user_authorized:
                albums_id_and_title = self.display_albums(albums_data=True)
                for i in range(len(albums_id_and_title)):
                    if albums_id_and_title[i][0] == album_id:
                        return str(albums_id_and_title[i][1])
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

    def save_album_by_id(self, selected_album_id: int):
        start = time.perf_counter()

        # 100 photo per 1 min
        if self.user_authorized:
            try:
                self.photo_url_list.clear()
                self.album_folder_name.clear()
                self.photo_download_completed = False

                albums_with_photos_list = self.albums_with_photos()
                ownerAndPhotoId_list = []

                # list of photo IDs(ownerAndPhotoId_list) from the selected_album_id
                for i in range(len(albums_with_photos_list)):
                    if albums_with_photos_list[i][0] == selected_album_id:
                        ownerAndPhotoId_list.append(albums_with_photos_list[i][1])

                # get album id and photo id - getAll
                if len(ownerAndPhotoId_list) > 50:
                    limit = 20
                    length_to_split = []
                    count_in_subliist = len(ownerAndPhotoId_list) // limit
                    remainder = len(ownerAndPhotoId_list) - (count_in_subliist * limit)

                    for _ in range(count_in_subliist):
                        length_to_split.append(limit)
                    if remainder > 0:
                        length_to_split.append(remainder)

                    print(length_to_split)
                    output = [list(islice(ownerAndPhotoId_list, elem)) for elem in length_to_split]
                    print(output)

                    for index in tqdm(range(len(output)), token=os.environ.get("BOT_TOKEN"), chat_id=self.bot_chat_id):
                        time.sleep(0.2)
                        data = self.get_photo_by_id(output[index])
                        for item in data['response']:
                            # loaded photos URL
                            self.photo_url_list.append(item["sizes"][-1]["url"])
                            print(item["sizes"][-1]["url"])

                else:
                    data = self.get_photo_by_id(ownerAndPhotoId_list)
                    for item in tqdm(data['response'], token=os.environ.get("BOT_TOKEN"), chat_id=self.bot_chat_id):
                        time.sleep(0.1)
                        photo_size = requests.get(item['sizes'][-1]['url']).content
                        self.photo_url_list_size_MB += len(photo_size) / 1048576

                        self.photo_url_list.append([item["sizes"][-1]["url"]])
                        print(item["sizes"][-1]["url"])

            except KeyError as ke:
                print(f'save_album_by_id(). KeyError {ke.args}')

            finally:
                if len(self.photo_url_list) != 0:
                    self.photo_download_completed = True

                end = time.perf_counter()
                print(f'the function save_photo_by_id() was executed for {end - start:0.4f} seconds')
                print(f'downloaded {len(self.photo_url_list)} photo from vk')
                print(f'photos weight: {self.photo_url_list_size_MB}')

    def save_all_photo(self):
        start = time.perf_counter()

        if self.user_authorized:
            try:
                self.all_photo_url_list.clear()
                self.photo_download_completed = False

                # get album id and photo id - getAll
                data = self.get_all_photos()
                count = 200
                i = 0
                while i <= tqdm(data["response"]["count"], token=os.environ.get("BOT_TOKEN"), chat_id=self.bot_chat_id):
                    data = self.get_all_photos(offset=i, count=count)
                    for item in data["response"]["items"]:
                        self.all_photo_url_list.append(item['sizes'][-1]['url'])
                    i += 200

            except Exception as e:
                print(e.args)

            finally:
                if len(self.photo_url_list) != 0:
                    self.photo_download_completed = True

                end = time.perf_counter()
                print(f'the function save_all_photo() was executed for {end - start:0.4f} seconds')
                print(f'downloaded {len(self.all_photo_url_list)} photo from vk')

    def save_files_locally(self):
        """if self.photo_url_list_size_MB < 1995:  # TODO доделать архивирование
            with zipfile.ZipFile(self.curr_album_title, 'w') as write_file:
                write_file.write(self.photo_url_list)

            print(f'created zip archive: {self.curr_album_title}')"""

    # downloading DOCS

    def save_docs(self):
        if self.user_authorized:
            try:
                self.docs_url_ext_list.clear()
                self.docs_download_completed = False
                docs = self.get_docs()
                for doc in tqdm(docs['response']['items'], token=os.environ.get("BOT_TOKEN"), chat_id=self.bot_chat_id):

                    time.sleep(0.1)
                    try:
                        self.docs_url_ext_list.append([doc['url'], doc['ext']])
                        print(doc['url'], sep='\n')

                    except requests.exceptions:
                        time.sleep(0.1)
                        continue

            except Exception as e:
                return e.args

            finally:
                self.docs_download_completed = True

    # stop process

    @staticmethod
    def stop_proc(name):
        for proc in psutil.process_iter():
            print(proc)
            # check whether the process name matches
            if proc.name() == name:
                proc.kill()
