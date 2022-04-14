import asyncio
import os
import time

import aiohttp
import requests
from tqdm.contrib.telegram import tqdm

from db.database import users_db


class DownloadVk:
    def __init__(self):
        self.vk_app_id: int = 8109852
        self.vk_api_v = 5.131
        self.redirect_uri = 'https://oauth.vk.com/close.html'
        self.scopes = "photos,docs"

    # authorization in user account

    def send_auth_link(self):
        # response_type=code!
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={self.vk_app_id}&display=page&" \
                     f"redirect_uri={self.redirect_uri}" \
                     f"&scope={self.scopes}&revoke=1&response_type=code&v={self.vk_api_v}"

        return oAuth_link

    async def auth_vk(self, user_id, vk_response: str):
        try:
            split_link = vk_response.split('#').copy()

            if split_link[0] == 'https://oauth.vk.com/blank.html':
                split_code = split_link[1].split('=')[-1:]
                code = split_code[0]  # The parameter code can be used within 1 hour to get
                # an access_token from your server.

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
                    return f'При авторизации произошла ошибка {get_access_token["response"]}'
            else:
                return f'Вы ввели некорректную информацию'
        except Exception as e:
            users_db["user"].upsert(
                {
                    "user_id": user_id,
                    "vk_user_authorized": False
                }, pk='user_id')
            return f"Ошибка авторизации в Vk! {e.args}"

    @staticmethod
    async def check_token(user_id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.vk.com/method/secure.checkToken',
                                       params={
                                           'access_token': os.environ.get('vk_app_service'),
                                           'token': users_db['user'].get(user_id).get('vk_token'),
                                           'v': 5.131
                                       }) as resp:
                    check = await resp.json()
                    try:
                        if check['error']:
                            print(f"user_id: {user_id} | checkToken: error_msg={check['error_msg']}")
                            return False

                    except KeyError:
                        if check['response']['success'] == 1:
                            print(f"user_id: {user_id} | checkToken: success={check['response']['success']}")
                            return True

        except KeyError as ke2:
            print(f'KeyError check_token(user_id: {user_id}): {ke2.args}')
            return False

    # get available scopes

    @staticmethod
    async def get_scopes(user_id):
        try:
            scopes_list = []
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.vk.com/method/apps.getScopes",
                                       params={
                                           'access_token': users_db['user'].get(user_id).get('vk_token'),
                                           'owner_id': 'user',
                                           'v': 5.131
                                       }) as resp:
                    print(f'get_scopes(): response_status: {resp.status}')

                    data = await resp.json()
                    i = 0
                    while i <= data["response"]["count"]:
                        for names in data["response"]["items"]:
                            scopes_list.append(names["items"]["name"])
                            scopes_list.append(',')
                            i += 1
                    return scopes_list

        except Exception as e:
            print(f'get_scopes(): {e.args}')
            return e.args

    # get JSON file with PHOTOS data

    @staticmethod
    async def get_photo_by_id_list(user_id: int, photo_ids: list):
        try:
            ids_str = str()
            owner_id = users_db['user'].get(user_id).get('vk_user_id')
            for item in photo_ids:
                ids_str += f",{owner_id}_{item}"
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.vk.com/method/photos.getById",
                                       params={
                                           'access_token': users_db['user'].get(user_id).get('vk_token'),
                                           'photos': ids_str,
                                           'v': 5.131}) as resp:
                    print(f'get_photo_by_id(): response_status: {resp.status}')
                    return await resp.json()
        except Exception as e:
            print(f'get_photo_by_id_list(): {e.args}')

    @staticmethod
    async def get_photo_by_id(user_id: int, photo_id: int):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.vk.com/method/photos.getById",
                                       params={
                                           'access_token': users_db['user'].get(user_id).get('vk_token'),
                                           'photos': f"{users_db['user'].get(user_id).get('vk_user_id')}_{photo_id}",
                                           'v': 5.131
                                       }) as resp:
                    print(f'get_photo_by_id(): response_status: {resp.status}')
                    return await resp.json()

        except Exception as e:
            print(f'get_thumb(): {e.args}')

    @staticmethod
    async def get_albums(user_id):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.vk.com/method/photos.getAlbums",
                                   params={
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'user_id': users_db['user'].get(user_id).get('vk_user_id'),
                                       'v': 5.131
                                   }) as resp:
                print(f'get_albums(): response_status: {resp.status}')
                return await resp.json()

    @staticmethod
    async def get_all_photos(user_id, offset=0, count=0):
        async with aiohttp.ClientSession() as session:
            await asyncio.sleep(0.02)
            async with session.get("https://api.vk.com/method/photos.getAll",
                                   params={
                                       'owner_id': users_db['user'].get(user_id).get('vk_user_id'),
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'offset': offset,
                                       'count': count,
                                       'photo_sizes': 1,
                                       'v': 5.131
                                   }) as resp:
                print(f'get_all_photos(): offset: {offset}, count: {count}, response_status: {resp.status}')
                return await resp.json()

    # get json file with DOCS data

    @staticmethod
    async def get_docs(user_id, count=0):
        """MAX count = 200"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.vk.com/method/docs.get",
                                   params={
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'count': count,
                                       'v': 5.131
                                   }) as resp:
                print(f'get_docs(): response_status: {resp.status}')
                return await resp.json()

    # get all PHOTOS by albums_id and photo_id

    async def photos_with_albums(self, user_id):
        start = time.perf_counter()
        try:
            # get album id and photo id - getAll
            data = await self.get_all_photos(user_id)
            album_id_photo_id = {}
            count = 200
            i = 0
            # tqdm(, token = os.environ.get("BOT_TOKEN"), chat_id = user_id):
            while i <= data["response"]["count"]:
                data = await self.get_all_photos(user_id, offset=i, count=count)
                for item in data["response"]["items"]:
                    album_id_photo_id[item["id"]] = item["album_id"]
                i += 200

            end = time.perf_counter()
            print(f'the function albums_with_photos() was executed for {end - start:0.4f} seconds')
            return album_id_photo_id.items()

        except Exception as e:
            return e.args

    async def display_album(self, user_id):
        try:
            json_data = await self.get_albums(user_id)
            albums_id_title_size_thumb = []
            for albums in json_data["response"]["items"]:
                if albums['size'] > 0:
                    thumb_url = await DownloadVk.get_photo_by_id(user_id, albums["thumb_id"])
                    albums_id_title_size_thumb.append([[albums["id"],
                                                        albums["title"],
                                                        albums["size"],
                                                        thumb_url['response'][0]['sizes'][2]['url']
                                                        ]])
            return albums_id_title_size_thumb

        except Exception as e:
            return e.args

    async def display_albums_id(self, user_id):
        try:
            json_data = await self.get_albums(user_id)
            albums_id = []
            for albums in json_data["response"]["items"]:
                albums_id.append(albums["id"])
            return albums_id

        except Exception as e:
            return e.args

    async def display_album_id_title(self, user_id):
        try:
            json_data = await self.get_albums(user_id)
            albums_id_title = []
            for albums in json_data["response"]["items"]:
                albums_id_title.append([albums["id"],
                                        albums["title"]])
            return albums_id_title

        except Exception as e:
            return e.args

    async def display_albums_title(self, user_id, album_id: int):
        try:
            albums_id_and_title = await self.display_album_id_title(user_id)
            for i in range(len(albums_id_and_title)):
                if albums_id_and_title[i][0] == album_id:
                    return str(albums_id_and_title[i][1])
        except Exception as e:
            return e.args

    """async def save_album_into_db(self, user_id):
        start = time.perf_counter()
        users_db[f"{user_id}_albums"].create(
            {
                "photo_id": int,
                "album_id": int,
            }, pk="photo_id", if_not_exists=True)

        photo_id_album_id_dict = self.photos_with_albums(user_id)

        # set of photo IDs(ownerAndPhotoId_list) from the selected_album_id
        for key, value in tqdm(photo_id_album_id_dict, token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
            users_db[f"{user_id}_albums"].insert_all(
                [
                    {
                        "photo_id": key,
                        "album_id": value
                    }
                ], pk="photo_id", replace=True)
        end = time.perf_counter()
        print(f'the function sorting_photos_into_albums() was executed for {end - start:0.4f} seconds')"""

    # downloading PHOTOS by album

    async def save_album_by_id(self, user_id, selected_album_id: int | list):
        start = time.perf_counter()

        users_db[f'{user_id}_photos'].drop()
        users_db[f"{user_id}_photos"].create(
            {
                "id": int,
                "photo_url": str,
                "photo_ext": str,
                "album_title": str,
            }, pk="id")

        users_db['user'].upsert(
            {
                "user_id": user_id,
                "vk_photo_download_completed": False,
                "number_downloaded_file": 0
            }, pk="user_id")

        if users_db['user'].get(user_id).get('vk_user_authorized'):
            count = 0
            album_title = await self.display_albums_title(user_id, selected_album_id)

            try:
                photo_id_album_id_dict = await self.photos_with_albums(user_id)
                photoIdOfSelectedAlbum = []
                # set of photo IDs(ownerAndPhotoId_list) from the selected_album_id
                if isinstance(selected_album_id, int):
                    for key, value in photo_id_album_id_dict:
                        if value == selected_album_id:
                            photoIdOfSelectedAlbum.append(key)

                elif isinstance(selected_album_id, list):
                    for key, value in photo_id_album_id_dict:
                        for item in selected_album_id:
                            if value == item:
                                photoIdOfSelectedAlbum.append(key)

                if len(photoIdOfSelectedAlbum) > 20:

                    # Split a list into Chunks using For Loops
                    chunked_list = list()
                    chunk_size = 20
                    for i in range(0, len(photoIdOfSelectedAlbum), chunk_size):
                        chunked_list.append(photoIdOfSelectedAlbum[i:i + chunk_size])

                    print(chunk_size)
                    print(chunked_list)

                    for index in tqdm(range(len(chunked_list)), token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
                        time.sleep(0.2)
                        data = await self.get_photo_by_id_list(user_id, chunked_list[index])
                        for item in data['response']:
                            # loaded photos URL
                            users_db[f"{user_id}_photos"].insert_all(
                                [
                                    {
                                        "id": count,
                                        "photo_url": item["sizes"][-1]["url"],
                                        "photo_ext": '.jpg',
                                        "album_title": album_title
                                    }
                                ], pk="id", replace=True)
                            count += 1

                            print(item["sizes"][-1]["url"])
                else:
                    data = await self.get_photo_by_id_list(user_id, photoIdOfSelectedAlbum)
                    for item in tqdm(data['response'], token=os.environ.get("BOT_TOKEN"),
                                     chat_id=user_id):
                        users_db[f"{user_id}_photos"].insert_all(
                            [
                                {
                                    "id": count,
                                    "photo_url": item["sizes"][-1]["url"],
                                    "photo_ext": '.jpg',
                                    "album_title": album_title
                                }
                            ], pk="id", replace=True)
                        count += 1
                        print(item["sizes"][-1]["url"])

            except KeyError as ke:
                print(f'save_album_by_id(). KeyError {ke.args}')

            finally:
                if users_db[f"{user_id}_photos"].count > 0:
                    users_db['user'].upsert(
                        {
                            "user_id": user_id,
                            "vk_photo_download_completed": True,
                            "number_downloaded_file": count

                        }, pk="user_id")
                end = time.perf_counter()
                print(f'the function save_photo_by_id() was completed in {end - start:0.4f} seconds')
                print(f'downloaded {users_db["user"].get(user_id).get("number_downloaded_file")}')

    # downloading DOCS

    async def save_docs(self, user_id):
        users_db[f'{user_id}_docs'].drop()
        users_db[f"{user_id}_docs"].create(
            {
                "id": int,
                "docs_url": str,
                "docs_ext": str,
                "title": str
            }, pk="id")

        users_db['user'].upsert(
            {
                "user_id": user_id,
                "vk_docs_download_completed": False,
                "number_downloaded_file": 0,
                "ya_upload_completed": False,
                "number_uploaded_file": 0
            }, pk="user_id")

        if users_db['user'].get(user_id).get('vk_user_authorized'):
            try:
                docs = await self.get_docs(user_id)
                count = 0
                for doc in tqdm(docs['response']['items'], token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
                    users_db[f"{user_id}_docs"].upsert(
                        {
                            "id": count,
                            "docs_url": doc["url"],
                            "docs_ext": f".{doc['ext']}",
                            "title": doc['title']
                        }, pk="id")
                    count += 1
                    print(doc['url'], sep='\n')

            except Exception as e:
                print(f'save_docs(). Exception {e.args}')
                return e.args
            finally:
                users_db['user'].upsert(
                    {
                        "user_id": user_id,
                        "vk_docs_download_completed": True,
                    }, pk="user_id")
