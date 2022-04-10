import json
import os
import time
from itertools import islice

import requests

from tqdm.contrib.telegram import tqdm

from db.database import users_db


class DownloadVk:
    def __init__(self):
        self.vk_app_id: int = 8109852
        self.vk_api_v = 5.131
        self.redirect_uri = 'https://oauth.vk.com/blank.html.com/blank.html'
        self.scopes = "photos,docs"

    # authorization in user account

    def send_auth_link(self):
        # response_type=code!
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={self.vk_app_id}&display=page&" \
                     f"redirect_uri={self.redirect_uri}" \
                     f"&scope={self.scopes}&response_type=code&v={self.vk_api_v}"

        return oAuth_link

    async def auth_vk(self, user_id, vk_response: str):
        try:
            split_link = vk_response.split('#').copy()
            code = ''  # The parameter code can be used within 1 hour to get
            # an access_token from your server.

            if split_link[0] == 'https://oauth.vk.com/blank.html':
                split_code = split_link[1].split('=')[-1:]
                code: str = split_code[0]

            get_access_token = requests.get('https://oauth.vk.com/access_token',
                                            params={
                                                'client_id': self.vk_app_id,
                                                'client_secret': os.environ.get('vk_app_secret'),
                                                'redirect_uri': self.redirect_uri,
                                                'code': code
                                            }).json()
            if get_access_token['access_token']:
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "vk_token": get_access_token['access_token'],
                        "vk_user_id": get_access_token['user_id'],
                        "vk_token_expires_in": get_access_token['expires_in'],
                        "vk_user_authorized": True,
                    }, pk='user_id')
                return 'Вы успешно авторизовались в VK!'
            else:
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "vk_user_authorized": False,
                    }, pk='user_id')
                return f'При авторизации произошла ошибка {get_access_token["error_description"]}'
        except Exception as e:
            users_db["user"].insert_all(
                {
                    "user_id": user_id,
                    "vk_user_authorized": False,
                }, pk='user_id')
            return f"Ошибка авторизации в Vk! {e.args}"

    @staticmethod
    def check_token(user_id):
        try:
            check = requests.get('https://oauth.vk.com/secure.checkToken',
                                 params={
                                     'access_token': users_db['user'].get(user_id).get('vk_token'),
                                     'token': os.environ.get('vk_app_secret')
                                 }).json()

            if check['success'] == 1:
                return True
            else:
                return False
        except Exception as e:
            return f'check_token(user_id): {e.args}'

    # get available scopes

    @staticmethod
    def get_scopes(user_id):
        try:
            scopes_list = []
            api = requests.get("https://api.vk.com/method/apps.getScopes", params={
                'access_token': users_db['user'].get(user_id).get('vk_token'),
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

    @staticmethod
    def get_photo_by_id(user_id: int, photo_id: list):
        id_list = ''
        for item in photo_id:
            id_list += ',' + str(users_db['user'].get(user_id).get('vk_user_id')) + '_' + str(item)

        api = requests.get("https://api.vk.com/method/photos.getById", params={
            'access_token': users_db['user'].get(user_id).get('vk_token'),
            'photos': id_list,
            'v': 5.131
        })
        return api.json()

    @staticmethod
    def get_albums(user_id):
        api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
            'access_token': users_db['user'].get(user_id).get('vk_token'),
            'v': 5.131
        })
        return json.loads(api.text)

    @staticmethod
    def get_albums_count(user_id):
        api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
            'access_token': users_db['user'].get(user_id).get('vk_token'),
            'user_id': users_db['user'].get(user_id).get('vk_user_id'),
            'v': 5.131
        })
        return json.loads(api.text)

    @staticmethod
    def get_all_photos(user_id, offset=0, count=0):
        api = requests.get("https://api.vk.com/method/photos.getAll", params={
            'owner_id': users_db['user'].get(user_id).get('vk_user_id'),
            'access_token': users_db['user'].get(user_id).get('vk_token'),
            'offset': offset,
            'count': count,
            'photo_sizes': 1,
            'v': 5.131
        })
        return json.loads(api.text)

    # get json file with DOCS data

    @staticmethod
    def get_docs(user_id, count=0):
        """MAX count = 200"""
        api = requests.get("https://api.vk.com/method/docs.get", params={
            'access_token': users_db['user'].get(user_id).get('vk_token'),
            'count': count,
            'v': 5.131
        })
        return json.loads(api.text)

    # sorting all PHOTOS by albums_id and photo_id

    def albums_with_photos(self, user_id):
        try:
            # get album id and photo id - getAll
            data = self.get_all_photos(user_id)
            album_id_photo_id = []
            count = 200
            i = 0
            while i <= data["response"]["count"]:
                data = self.get_all_photos(user_id, offset=i, count=count)
                for item in data["response"]["items"]:
                    album_id_photo_id.append([item["album_id"], item["id"]])
                i += 200
            return album_id_photo_id

        except Exception as e:
            return e.args

    def display_album_id_title(self, user_id):
        try:
            json_data = self.get_albums(user_id)
            albums_id_title = []
            for albums in json_data["response"]["items"]:
                albums_id_title.append([albums["id"], albums["title"]])
            return albums_id_title

        except Exception as e:
            return e.args

    def display_album_thumb(self, user_id):
        try:
            json_data = self.get_albums(user_id)
            albums_id_title_size_thumb = []
            for albums in json_data["response"]["items"]:
                albums_id_title_size_thumb.append([[albums["id"],
                                                    albums["title"],
                                                    albums["size"],
                                                    albums["thumb_id"]]])
            return albums_id_title_size_thumb

        except Exception as e:
            return e.args

    def display_albums_title(self, user_id, album_id: int):
        try:
            albums_id_and_title = self.display_album_id_title(user_id)
            for i in range(len(albums_id_and_title)):
                if albums_id_and_title[i][0] == album_id:
                    return str(albums_id_and_title[i][1])
        except Exception as e:
            return e.args

    def display_albums_id(self, user_id):
        try:
            json_data = self.get_albums(user_id)
            albums_id = []
            for albums in json_data["response"]["items"]:
                albums_id.append(albums["id"])
            return albums_id

        except Exception as e:
            return e.args

    # downloading PHOTOS by album

    async def save_album_by_id(self, user_id, selected_album_id: int):
        start = time.perf_counter()

        if users_db[f'{user_id}'].exists():
            users_db[f'{user_id}'].drop()

        users_db['user'].upsert(
            {
                "user_id": user_id,
                "vk_photo_download_completed": False,
                "number_downloaded_file": 0
            }, pk="user_id")

        # 100 photo per 1 min
        if users_db['user'].get(user_id).get('vk_user_authorized'):
            count = 0
            try:
                albums_with_photos_list = self.albums_with_photos(user_id)
                ownerAndPhotoIdList = []

                # list of photo IDs(ownerAndPhotoId_list) from the selected_album_id
                for i in range(len(albums_with_photos_list)):
                    if albums_with_photos_list[i][0] == selected_album_id:
                        ownerAndPhotoIdList.append(albums_with_photos_list[i][1])

                # get album id and photo id - getAll
                if len(ownerAndPhotoIdList) > 50:
                    limit = 20
                    length_to_split = []
                    count_in_subliist = len(ownerAndPhotoIdList) // limit
                    remainder = len(ownerAndPhotoIdList) - (count_in_subliist * limit)

                    for _ in range(count_in_subliist):
                        length_to_split.append(limit)
                    if remainder > 0:
                        length_to_split.append(remainder)
                    print(length_to_split)

                    # split photo_id list to sublists of size length_to_split
                    output = [list(islice(ownerAndPhotoIdList, elem)) for elem in length_to_split]
                    print(output)

                    for index in tqdm(range(len(output)), token=os.environ.get("BOT_TOKEN"),
                                      chat_id=users_db['user'].get(user_id).get('chat_id')):

                        time.sleep(0.2)
                        data = self.get_photo_by_id(user_id, output[index])
                        for item in data['response']:
                            # loaded photos URL
                            users_db[f"{user_id}"].insert_all(
                                [
                                    {
                                        "id": count,
                                        "photo_url": (item["sizes"][-1]["url"]),
                                        "photo_ext": '.jpg'
                                    }
                                ], pk="id", replace=True)
                            count += 1

                            print(item["sizes"][-1]["url"])
                else:
                    data = self.get_photo_by_id(user_id, ownerAndPhotoIdList)
                    album_title = self.display_albums_title(user_id, selected_album_id)
                    for item in tqdm(data['response'], token=os.environ.get("BOT_TOKEN"),
                                     chat_id=users_db['user'].get(user_id).get('chat_id')):
                        users_db[f"{user_id}"].insert_all(
                            [
                                {
                                    "id": count,
                                    "photo_url": (item["sizes"][-1]["url"]),
                                    "photo_ext": '.jpg',
                                    "album_title": album_title
                                }
                            ], pk="id", replace=True)
                        count += 1
                        print(item["sizes"][-1]["url"])

            except KeyError as ke:
                print(f'save_album_by_id(). KeyError {ke.args}')

            finally:
                if users_db[f"{user_id}"].count.bit_count() > 0:
                    users_db['user'].upsert(
                        {
                            "user_id": user_id,
                            "vk_photo_download_completed": True,
                            "number_downloaded_file": count

                        }, pk="user_id")
                end = time.perf_counter()
                print(f'the function save_photo_by_id() was executed for {end - start:0.4f} seconds')
                print(f'downloaded {users_db["user"].get(user_id).get("number_downloaded_file")}')

    """def save_all_photo(self, user_id):
        start = time.perf_counter()

        if self.user_authorized:
            try:
                self.all_photo_url_list.clear()
                self.vk_photo_download_completed = False

                # get album id and photo id - getAll
                data = self.get_all_photos(user_id)
                count = 200
                i = 0
                while i <= tqdm(data["response"]["count"], token=os.environ.get("BOT_TOKEN"), chat_id=self.bot_chat_id):
                    data = self.get_all_photos(user_id, offset=i, count=count)
                    for item in data["response"]["items"]:
                        self.all_photo_url_list.append([item['sizes'][-1]['url'], '.jpg'])
                    i += 200

            except Exception as e:
                print(e.args)

            finally:
                if len(self.photo_url_ext) != 0:
                    self.vk_photo_download_completed = True

                end = time.perf_counter()
                print(f'the function save_all_photo() was executed for {end - start:0.4f} seconds')
                print(f'downloaded {len(self.all_photo_url_list)} photo from vk')"""

    # downloading DOCS

    def save_docs(self, user_id):
        if users_db['user'].get(user_id).get('vk_user_authorized'):
            try:
                docs = self.get_docs(user_id)
                for doc in tqdm(docs['response']['items'], token=os.environ.get("BOT_TOKEN"),
                                chat_id=users_db['user'].get(user_id).get('chat_id')):

                    time.sleep(0.1)
                    try:
                        users_db[f"{user_id}"].upsert(
                            {
                                "docs_url": doc["sizes"][-1]["url"],
                                "docs_ext": doc['ext'],
                            })
                        print(doc['url'], sep='\n')
                    except requests.exceptions:
                        time.sleep(0.1)
                        continue

            except Exception as e:
                return e.args

            finally:
                users_db[f"{user_id}"].upsert(
                    {
                        "id": 1,
                        "vk_docs_download_completed": True,
                    }, pk="id")
