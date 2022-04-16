import asyncio
import os
import time

import aiohttp
from tqdm.contrib.telegram import tqdm

from db.database import users_db


class YandexDisk:
    def __init__(self):
        self.APP_ID = '131f4986553d493184f6a5e5af832174'
        self.URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.ROOT_FOLDER = 'Saved from tg'

    # authorization

    def send_link(self):

        link = f'https://oauth.yandex.ru/authorize?response_type=token' \
               f'&client_id={self.APP_ID}'
        return link

    @staticmethod
    async def auth(user_id, ya_token: str):
        if len(ya_token) == 39:
            users_db["user"].upsert(
                {
                    "user_id": user_id,
                    "y_api_token": ya_token,
                    "ya_user_authorized": True,
                }, pk='user_id')
            return 'Вы успешно авторизовались в Яндекс диске!'
        else:
            users_db["user"].upsert(
                {
                    "user_id": user_id,
                    "ya_user_authorized": False,
                }, pk='user_id')
            return 'Ошибка авторизации в Яндекс диске!'

    # actions with user disk

    async def get_folders(self, user_id):
        """'path': f'{self.ROOT_FOLDER}/'"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL,
                                   params={
                                       'path': f'{self.ROOT_FOLDER}/'
                                   },
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Accept': 'application/json',
                                       f'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                   }) as resp:
                print(f'get_folders(user_id: {user_id}): response_status: {resp.status}')
                return await resp.json()

    async def create_folder(self, user_id, folder_name):
        status = 0
        count = 0
        while status != 201:
            await asyncio.sleep(0.02)
            async with aiohttp.ClientSession() as session:
                async with session.put(f'{self.URL}?',
                                       params={
                                           'path': folder_name
                                       },
                                       data=None,
                                       headers={
                                           'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                       }) as resp:
                    status = resp.status
                    count += 1
                    print(f'user_id: {user_id}. Try create dir "{folder_name}" in cloud storage.'
                          f' Response code: {str(resp.status)}. Message: {await resp.json()}')
            if status == 201:
                return True
            if status == 423:
                continue
            if status == 409:
                await self.delete_folder(user_id, folder_name)
            else:
                return False

    async def delete_folder(self, user_id, folder_name):
        status = 0
        count = 0
        while status != 200 or 202 or 204:
            await asyncio.sleep(0.02)
            async with aiohttp.ClientSession() as session:
                async with session.delete(f'{self.URL}?',
                                          params={
                                              'path': f'{folder_name}',
                                              'permanently': 'True'
                                          },
                                          headers={
                                              'Content-Type': 'application/json',
                                              'Accept': 'application/json',
                                              'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                          }) as resp:
                    status = resp.status
                    count += 1
                    print(f'user_id: {user_id}. Try delete dir "{folder_name}" in cloud storage.'
                          f' Response code: {str(resp.status)}. Message: {await resp.json()}')
            if status == 200 or 202 or 204:
                return True
            if status == 423:
                continue
            else:
                return False

    async def upload_file(self, user_id: int, url_list: list, folder_name: str, overwrite: bool = False):
        """
        :param user_id: int
        :param url_list: [[url],[ext]]
        :param folder_name: str
        :param overwrite: bool
        """
        start = time.perf_counter()

        users_db['user'].upsert(
            {
                "user_id": user_id,
                "ya_upload_completed": False,
                "number_uploaded_file": 0
            }, pk="user_id")
        start_dir = time.perf_counter()
        subfolder_path = f'{self.ROOT_FOLDER}/{folder_name}'
        is_subfolder = False
        if await self.create_folder(user_id, self.ROOT_FOLDER):
            if await self.create_folder(user_id, subfolder_path):
                is_subfolder = True
        end_dir = time.perf_counter()
        print(f'user_id: {user_id}. Directory creation was done in {end_dir - start_dir:0.4f} seconds')

        if is_subfolder:
            counter = 0
            for i in tqdm(range(len(url_list)), token=os.environ.get("BOT_TOKEN"),
                          chat_id=user_id):
                try:
                    filename = str(counter + 1) + '_file'
                    await asyncio.sleep(0.02)
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{self.URL}/upload?",
                                                params={
                                                    'path': f'{subfolder_path}/{filename}{url_list[i][1]}',
                                                    'url': url_list[i][0],
                                                    'overwrite': str(overwrite)
                                                },
                                                data=None,
                                                headers={
                                                    'Content-Type': 'application/json',
                                                    'Accept': 'application/json',
                                                    'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                                }) as resp:
                            counter += 1
                            print(f" album: {folder_name} | status: {resp.status}")

                except aiohttp.ClientConnectorError:
                    await asyncio.sleep(0.07)
                    continue

            users_db['user'].upsert(
                {
                    "user_id": user_id,
                    "number_uploaded_file": counter
                }, pk="user_id")

            if len(url_list) == users_db["user"].get(user_id).get("number_uploaded_file") \
                    or (len(url_list) - users_db["user"].get(user_id).get("number_uploaded_file")) < 20:
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "ya_upload_completed": True,
                    }, pk='user_id')
            else:
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "ya_upload_completed": False,
                    }, pk='user_id')

        end = time.perf_counter()
        print(f'\nthe function upload_file(user_id: {user_id}) was completed in {end - start:0.4f} seconds')
        print(f'uploaded {users_db["user"].get(user_id).get("number_uploaded_file")}')

    async def get_published_file(self, user_id, folder_name):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/public",
                                   params={
                                       'path': f"{self.ROOT_FOLDER}/{folder_name}",
                                       'type': 'dir',
                                       'preview_crop': 'true'
                                   },
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Accept': 'application/json',
                                       'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                   }) as resp:
                print(f'user_id: {user_id}. Get published folder: {self.ROOT_FOLDER}/{folder_name}. Response: {resp.status}')
                if resp.status == 200:
                    return await resp.json()
                else:
                    error = await resp.json()
                    return error['descriptions']

    async def get_link_to_file(self, user_id, folder_name: str):
        if users_db["user"].get(user_id).get("ya_upload_completed"):
            try:
                async with aiohttp.ClientSession() as session0:
                    async with session0.put(f"{self.URL}/publish",
                                            params={
                                                'path': f"{self.ROOT_FOLDER}/{folder_name}"
                                            },
                                            data=None,
                                            headers={
                                                'Content-Type': 'application/json',
                                                'Accept': 'application/json',
                                                'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                            }) as put_resp:
                        print(f'user_id: {user_id}. Publish folder: {self.ROOT_FOLDER}/{folder_name}. Response: {put_resp.status}')

            except KeyError as ke:
                print(f'get_link_file(user_id: {user_id}) KeyError' + str(ke.args))
                return f'get_link_file() KeyError {ke.args}'
            finally:
                published = await self.get_published_file(user_id, folder_name)
                if published:
                    for item in published['items']:
                        if item['name'] == folder_name:
                            return item['public_url']
                else:
                    return 'При получении ссылки на опубликованный ресурс произошла ошибка'
        else:
            return f'get_link_file(user_id: {user_id}): ya_upload_completed: 0'
