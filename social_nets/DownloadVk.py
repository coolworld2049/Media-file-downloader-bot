import asyncio
import os
import time
from abc import abstractmethod

from aiohttp import ClientSession as clientSession, ClientConnectorError as clientConnectorError
from tqdm.contrib.telegram import tqdm

from core import users_db


class DownloadVk:
    def __init__(self):
        self.vk_app_id = 8109852
        self.vk_api_v = 5.131
        self.scopes = "photos,docs"
        self.redirect_uri = 'https://oauth.vk.com/blank.html'

    # ----authorization----

    @abstractmethod
    def link(self):
        # response_type=code!
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={self.vk_app_id}&display=page&" \
                     f"redirect_uri={self.redirect_uri}" \
                     f"&scope={self.scopes}&revoke=1&response_type=code&v={self.vk_api_v}"

        return oAuth_link

    @abstractmethod
    async def auth(self, user_id, vk_response: str):
        split_link = vk_response.split('#').copy()
        if split_link[0] == 'https://oauth.vk.com/blank.html':
            code = split_link[1].split('=')[-1:][0]

            async with clientSession() as session:
                async with session.get('https://oauth.vk.com/access_token',
                                       params={
                                           'client_id': self.vk_app_id,
                                           'client_secret': os.environ.get('vk_app_secret'),
                                           'redirect_uri': self.redirect_uri,
                                           'code': code
                                       }) as resp:
                    get_access_token = await resp.json()

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
                return f'При авторизации произошла ошибка {get_access_token["response"]}'
        else:
            return f'Вы ввели некорректную информацию'

    @abstractmethod
    async def check_token(self, user_id):
        try:
            async with clientSession() as session:
                async with session.get('https://api.vk.com/method/secure.checkToken',
                                       params={
                                           'access_token': os.environ.get('vk_app_service'),
                                           'token': users_db['user'].get(user_id).get('vk_token'),
                                           'v': self.vk_api_v
                                       }) as resp:
                    check = await resp.json()
                    try:
                        if check['error']:
                            print(f"user_id: {user_id}. checkToken: error_msg={check['error_msg']}")
                            return False
                    except KeyError:
                        if check['response']['success'] == 1:
                            print(f"user_id: {user_id}. checkToken: success="
                                  f"{check['response']['success']}")
                            return True
        except KeyError as ke2:
            print(f'user_id: {user_id}. User is not authorized check_token'
                  f'(user_id: {user_id}): {ke2.args}')
            return False

    # ----vk api requests----

    async def request_get_all_photos(self, user_id, offset=0, count=0):
        async with clientSession() as session:
            async with session.get("https://api.vk.com/method/photos.getAll",
                                   params={
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'owner_id': users_db['user'].get(user_id).get('vk_user_id'),
                                       'offset': offset,
                                       'count': count,
                                       'photo_sizes': 1,
                                       'v': self.vk_api_v
                                   }) as resp:
                print(f'request_get_all_photos(user_id: {user_id}): offset: {offset}, count: {count},'
                      f' response_status: {resp.status}')
                return await resp.json()

    async def request_get_service_albums(self, user_id, service_album_id: int, offset=0, count=0):
        async with clientSession() as session:
            async with session.get("https://api.vk.com/method/photos.get",
                                   params={
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'owner_id': users_db['user'].get(user_id).get('vk_user_id'),
                                       'album_id': str(service_album_id),
                                       'offset': offset,
                                       'count': count,
                                       'photo_sizes': 1,
                                       'v': self.vk_api_v
                                   }) as resp:
                print(f'request_get_service_albums(user_id: {user_id}): offset: {offset}, count: {count},'
                      f' service_album_id: {service_album_id}), response_status: {resp.status}')
                return await resp.json()

    # @profile(stream=fp, precision=4)
    async def request_get_photo_by_id(self, user_id: int, photo_id: int | list):
        photo = str()
        owner_id = users_db['user'].get(user_id).get('vk_user_id')
        if isinstance(photo_id, list):
            for item in photo_id:
                photo += f",{owner_id}_{item}"
        elif isinstance(photo_id, int):
            photo = f"{owner_id}_{photo_id}"
        try:
            async with clientSession() as session:
                async with session.get("https://api.vk.com/method/photos.getById",
                                       params={
                                           'access_token':
                                               users_db['user'].get(user_id).get('vk_token'),
                                           'photos': photo,
                                           'v': self.vk_api_v
                                       }) as resp:
                    return await resp.json()
        except clientConnectorError as ke:
            print(f'user_id: {user_id}. get_photo_by_id(user_id: {user_id})'
                  f'Connection Error: {ke.args}')
        print(f'request_get_photo_by_id(user_id: {user_id}): response_status: {resp.status}')

    async def request_get_albums(self, user_id):
        async with clientSession() as session:
            async with session.get("https://api.vk.com/method/photos.getAlbums",
                                   params={
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'user_id': users_db['user'].get(user_id).get('vk_user_id'),
                                       'need_system': 1,
                                       'v': self.vk_api_v
                                   }) as resp:
                print(f'request_get_albums(user_id: {user_id}): response_status: {resp.status}')
                return await resp.json()

    async def request_get_docs(self, user_id):
        """:return: max 2000 docs items"""
        async with clientSession() as session:
            async with session.get("https://api.vk.com/method/docs.get",
                                   params={
                                       'access_token': users_db['user'].get(user_id).get('vk_token'),
                                       'v': self.vk_api_v
                                   }) as resp:
                print(f'request_get_docs(user_id: {user_id}): response_status: {resp.status}')
                return await resp.json()

    # ----processing response from vk api----

    # @profile(stream=fp, precision=4)
    async def get_photo_id_album_id(self, user_id):
        """get all photos using await self.get_all_photos(user_id)
        using await self.get_all_photos(user_id)"""
        start = time.perf_counter()
        try:
            data = await self.request_get_all_photos(user_id)
            photo_id_album_id = {}
            count = 200
            offset = 0
            while offset <= data["response"]["count"]:
                data = await self.request_get_all_photos(user_id, offset=offset, count=count)
                for item in data["response"]["items"]:
                    photo_id_album_id[item["id"]] = item["album_id"]
                offset += 200
            return photo_id_album_id.items()
        except Exception as e:
            return e.args
        finally:
            end = time.perf_counter()
            print(f'the function get_photo_id_album_id(user_id: {user_id}) was executed in {end - start:0.4f} seconds')

    # @profile(stream=fp, precision=4)
    async def get_service_albums(self, user_id, service_album_id: int):
        """get photos from service album(saved, wall, profile) using
         await self.request_get_service_albums(user_id, service_album_id)"""
        start = time.perf_counter()
        try:
            data = await self.request_get_service_albums(user_id, service_album_id)
            photo_id_service_album_id = {}
            count = 200
            offset = 0
            while offset <= data["response"]["count"]:
                data = await self.request_get_service_albums(user_id, service_album_id, offset=offset, count=count)
                for item in data["response"]["items"]:
                    photo_id_service_album_id[item["id"]] = item["album_id"]
                offset += 200
            return photo_id_service_album_id.items()
        except Exception as e:
            return e.args
        finally:
            end = time.perf_counter()
            print(f'the function get_service_albums(user_id: {user_id}, album_id: {service_album_id})'
                  f' was executed in {end - start:0.4f} seconds')

    async def get_album_attrs(self, user_id):
        """:return: [[id], [title], [size], [thumb_id]]"""
        try:
            json_data = await self.request_get_albums(user_id)
            albums_id_title_size_thumb = \
                [
                    [
                        albums["id"], albums["title"], albums["size"], albums['thumb_id']
                    ]
                    for albums in json_data["response"]["items"]
                    if albums['size'] > 0
                ]
            return albums_id_title_size_thumb
        except Exception as e:
            return e.args
        finally:
            print(f'get_album_attrs(user_id: {user_id})')

    async def get_album_id(self, user_id):
        """:return: [[id]]"""
        try:
            json_data = await self.request_get_albums(user_id)
            albums_id = \
                [
                    albums_id["id"] for albums_id in json_data["response"]["items"]
                ]
            return albums_id
        except Exception as e:
            return e.args
        finally:
            print(f'get_album_id(user_id: {user_id}')

    async def get_album_id_title(self, user_id):
        """:return: [[id], [title]]"""
        try:
            json_data = await self.request_get_albums(user_id)
            albums_id_title = \
                {
                    str(albums["id"]): albums["title"] for albums in json_data["response"]["items"]
                }
            return albums_id_title.items()
        except Exception as e:
            print(f'get_album_id_title(user_id: {user_id}).'
                  f' Exception {e.args}')
            return e.args
        finally:
            print(f'get_album_id_title(user_id: {user_id}')

    async def get_album_title(self, user_id, album_id: int | str):
        """:return: title"""
        try:
            json_data = await self.get_album_id_title(user_id)
            for key, value in json_data:
                if key == str(album_id):
                    return value
        except Exception as e:
            print(f'display_albums_title(user_id: {user_id}, album_id: {album_id}).'
                  f' Exception {e.args}')
            return e.args
        finally:
            print(f'get_album_title(user_id: {user_id}, album_id: {album_id}')

    # @profile(stream=fp, precision=4)
    async def upsert_all_photo_into_db(self, user_id):
        if not users_db[f"{user_id}_all_photos"].exists():
            start = time.perf_counter()
            photo_id_album_id_dict = await self.get_photo_id_album_id(user_id)
            start_insert = time.perf_counter()
            for key, value in tqdm(photo_id_album_id_dict, token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
                users_db[f"{user_id}_all_photos"].insert_all(
                    [
                        {
                            "photo_id": key,
                            "album_id": value
                        }
                    ], pk="photo_id", replace=True)
            end_insert = time.perf_counter()
            end = time.perf_counter()
            print(f'users_db[f"{user_id}_all_photos"].insert_all was executed'
                  f' in {end_insert - start_insert:0.4f} seconds')
            print(f'the function insert_all_photos_into_db(user_id: {user_id}) '
                  f'was executed in {end - start:0.4f} seconds')
            return True
        else:
            return False

    # @profile(stream=fp, precision=4)
    async def get_photos_urls(self, user_id, album_title: str, photoIdsOfSelectedAlbum: list):
        start = time.perf_counter()
        count = 0
        data = await self.request_get_photo_by_id(user_id, photoIdsOfSelectedAlbum)
        for item in tqdm(data['response'], token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
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
        users_db['user'].upsert(
            {
                "total_number_downloaded_file":
                    users_db["user"].get(user_id).get("total_number_downloaded_file") + count
            }, pk="user_id")
        end = time.perf_counter()
        print(f'the function request_get_photo_url(user_id: {user_id}) '
              f'was completed in {end - start:0.4f} seconds')
        print(f'downloaded {users_db["user"].get(user_id).get("total_number_downloaded_file")}')

    @staticmethod
    async def wrapper(delay, coro):
        await asyncio.sleep(delay)
        return await coro

    # @profile(stream=fp, precision=4)
    async def get_photos_urls_by_chunks(self, user_id, album_title: str, photoIdsOfSelectedAlbum: list,
                                        chunk_size: int):
        start = time.perf_counter()
        count = 0
        chunked_list = [photoIdsOfSelectedAlbum[i:i + chunk_size]
                        for i in range(0, len(photoIdsOfSelectedAlbum), chunk_size)]
        for index in tqdm(range(len(chunked_list)), token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
            data = await DownloadVk().wrapper(0.3, self.request_get_photo_by_id(user_id, chunked_list[index]))
            for item in data['response']:
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
        users_db['user'].upsert(
            {
                "total_number_downloaded_file":
                    users_db["user"].get(user_id).get("total_number_downloaded_file") + count
            }, pk="user_id")
        end = time.perf_counter()
        print(f'the function request_get_photo_url_by_chunks(user_id: {user_id}) '
              f'was completed in {end - start:0.4f} seconds')
        print(f'downloaded {users_db["user"].get(user_id).get("total_number_downloaded_file")}')

    # @profile(stream=fp, precision=4)
    async def download_selected_album(self, user_id, selected_album_id: int | str | list, chunk_size=50):
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
            }, pk="user_id")

        if users_db['user'].get(user_id).get('vk_user_authorized'):
            start_get_all_photos = time.perf_counter()
            album_title = await self.get_album_title(user_id, selected_album_id)
            photoIdsOfSelectedAlbum = [None]
            match type(selected_album_id).__name__:
                case 'int':
                    photoIdsOfSelectedAlbum = [key for key, value in
                                               await self.get_photo_id_album_id(user_id)
                                               if value == selected_album_id]
                case 'str':
                    photoIdsOfSelectedAlbum = [key for key, value in
                                               await self.get_service_albums(user_id, int(selected_album_id))
                                               if str(value) == selected_album_id]
                    album_title = 'Saved photos'
                case 'list':
                    data = await self.get_photo_id_album_id(user_id)
                    photoIdsOfSelectedAlbum = list(data.mapping.keys())
                    for album_id in await self.get_album_id(user_id):
                        if album_id in selected_album_id:
                            srv_data = await self.get_service_albums(user_id, album_id)
                            photoIdsOfSelectedAlbum += list(srv_data.mapping.keys())
                    album_title = 'All photos'

            if photoIdsOfSelectedAlbum is not None:
                if len(photoIdsOfSelectedAlbum) >= chunk_size:
                    await self.get_photos_urls_by_chunks(user_id, album_title, photoIdsOfSelectedAlbum, chunk_size)
                else:
                    await DownloadVk().get_photos_urls(user_id, album_title, photoIdsOfSelectedAlbum)
                if users_db[f"{user_id}_photos"].count > 0:
                    users_db['user'].upsert(
                        {
                            "user_id": user_id,
                            "vk_photo_download_completed": True,
                        }, pk="user_id")
                end_get_all_photos = time.perf_counter()
                print(f'user_id: {user_id}. photoIdsOfSelectedAlbum.append(key)'
                      f' was completed in {end_get_all_photos - start_get_all_photos:0.4f} seconds')
            else:
                print(f'user_id: {user_id}. download_selected_album(user_id: {user_id},'
                      f' selected_album_id: {selected_album_id}.'
                      f' При получении альбома возникла ошибка')
                return 'При получении альбома возникла ошибка'

    # @profile(stream=fp, precision=4)
    async def download_docs(self, user_id):
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
                "ya_upload_completed": False,
            }, pk="user_id")

        if users_db['user'].get(user_id).get('vk_user_authorized'):
            try:
                docs = await self.request_get_docs(user_id)
                if docs['response']['count'] > 0:
                    count = 0
                    for doc in tqdm(docs['response']['items'], token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
                        users_db[f"{user_id}_docs"].insert_all(
                            [
                                {
                                    "id": count,
                                    "docs_url": doc["url"],
                                    "docs_ext": f".{doc['ext']}",
                                    "title": doc['title']
                                }
                            ], pk="id", replace=True)
                        count += 1
                        print(doc['url'], sep='\n')
                    if users_db[f"{user_id}_docs"].count > 0:
                        users_db['user'].upsert(
                            {
                                "user_id": user_id,
                                "vk_docs_download_completed": True,
                            }, pk="user_id")
                else:
                    return 'На вашем аккаунте отсутствуют документы'
            except Exception as e:
                print(f'save_docs(user_id: {user_id}). Exception {e.args}')
                return f'{e.args}'
