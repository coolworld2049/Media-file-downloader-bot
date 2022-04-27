import asyncio
import os
import time
from abc import abstractmethod

import nest_asyncio
from aiohttp import ClientSession as clientSession, ClientConnectorError
from tqdm.contrib.telegram import tqdm

from core import users_db


class YandexDisk:
    def __init__(self):
        self.RESOURCES_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.ROOT_FOLDER = 'Saved from tg'

    # ----authorization---

    @staticmethod
    @abstractmethod
    def link():
        link = f'https://oauth.yandex.ru/authorize?&response_type=code' \
               f'&client_id={os.environ.get("ya_client_id")}'
        return link

    @staticmethod
    @abstractmethod
    async def auth(user_id, ya_token: str):
        async with clientSession() as session:
            async with session.post('https://oauth.yandex.ru/token',
                                    data={
                                        'grant_type': 'authorization_code',
                                        'code': ya_token,
                                        'client_id': os.environ.get('ya_client_id'),
                                        'client_secret': os.environ.get('ya_client_secret')
                                    }) as resp:
                get_access_token = await resp.json()

            if resp.status == 200:
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "y_api_token": get_access_token['access_token'],
                        "ya_user_authorized": True,
                    }, pk='user_id')
                return 'Вы успешно авторизовались в Яндекс диске!'
            else:
                return f'Ошибка авторизации: {resp.status} в Яндекс диске!'

    @staticmethod
    # @profile(stream=fp, precision=4)
    async def request_upload_worker(url: str, params: dict, data: str, headers: dict):
        async with clientSession() as session:
            async with session.post(url=url, params=params, data=data, headers=headers):
                await session.close()

    @staticmethod
    async def wrapper(delay, coro):
        await asyncio.sleep(delay)
        return await coro

    # @profile(stream=fp, precision=4)
    async def multitask_post_requests(self, user_id: int, data: dict, folder_name: str, overwrite: bool = False):
        counter = 0
        subfolder_path = f'{self.ROOT_FOLDER}/{folder_name}'
        requests_dict = {}
        for url, ext in data.items():
            requests_dict[counter] = {
                'url': f"{self.RESOURCES_URL}/upload",
                'params': {
                    'path': f'{subfolder_path}/{counter + 1}_file{ext}',
                    'url': url,
                    'fields': 'href',
                    'overwrite': f'{overwrite}'
                },
                'data': None,
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                }}
            counter += 1

        chunk_size = 10
        requests_list = [value for key, value in requests_dict.items()]
        list_of_chunks = [requests_list[i:i + chunk_size]
                          for i in range(0, len(requests_list), chunk_size)]
        if len(requests_dict) >= chunk_size:
            tasks = []
            nest_asyncio.apply()
            loop = asyncio.get_running_loop()
            for i in tqdm(range(len(list_of_chunks)), token=os.environ.get("BOT_TOKEN"),
                          chat_id=user_id):
                for ch_items in list_of_chunks[i]:
                    tasks.append(loop.create_task(
                            self.wrapper(0.03, self.request_upload_worker(
                                ch_items['url'],
                                ch_items['params'],
                                ch_items['data'],
                                ch_items['headers']))))
                await asyncio.sleep(1.1)
                for k in range(len(tasks)):
                    loop.run_until_complete(tasks[i])
                    print(f'Task {k} run_until_complete: {tasks[k]}')

    # ----yandex disk api requests----

    # @profile(stream=fp, precision=4)
    async def request_create_folder(self, user_id, folder_name):
        status = 0
        count = 0
        while status != 201:
            await asyncio.sleep(0.02)
            async with clientSession() as session:
                async with session.put(f'{self.RESOURCES_URL}?',
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
            match status:
                case 201:
                    return True
                case 423:
                    continue
                case 404:
                    await self.request_create_folder(user_id, self.ROOT_FOLDER)
                case 409:
                    if folder_name == self.ROOT_FOLDER:
                        return True
                    else:
                        await self.request_delete_folder(user_id, folder_name)
                case _:
                    return False

    # @profile(stream=fp, precision=4)
    async def request_delete_folder(self, user_id, folder_name):
        status = 0
        count = 0
        while status != 200 or 202 or 204:
            await asyncio.sleep(0.05)
            async with clientSession() as session:
                async with session.delete(f'{self.RESOURCES_URL}?',
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
            match status:
                case 200 | 202 | 204:
                    return True
                case 423:
                    continue
                case _:
                    return False

    async def request_publish(self, user_id, folder_name: str):
        if users_db["user"].get(user_id).get("ya_upload_completed"):
            try:
                async with clientSession() as session:
                    async with session.put(f"{self.RESOURCES_URL}/publish",
                                           params={
                                               'path': f"{self.ROOT_FOLDER}/{folder_name}"
                                           },
                                           data=None,
                                           headers={
                                               'Content-Type': 'application/json',
                                               'Accept': 'application/json',
                                               'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                           }) as put_resp:
                        print(f'user_id: {user_id}. Publish folder: {self.ROOT_FOLDER}/{folder_name}.'
                              f' Response: {put_resp.status}')

            except KeyError as ke:
                print(f'get_link_file(user_id: {user_id}) KeyError' + str(ke.args))
                return f'get_link_file() KeyError {ke.args}'
            finally:
                published = await self.request_public(user_id, folder_name)
                if published:
                    for item in published['items']:
                        if item['name'] == folder_name:
                            return item['public_url']
                else:
                    return 'При получении ссылки на опубликованный ресурс произошла ошибка'
        else:
            return f'get_link_file(user_id: {user_id}): ya_upload_completed: 0'

    async def request_public(self, user_id, folder_name: str = ''):
        """get_published_file"""
        async with clientSession() as session:
            async with session.get(f"{self.RESOURCES_URL}/public",
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
                print(f'user_id: {user_id}. Get published folder: {self.ROOT_FOLDER}/{folder_name}.'
                      f' Response: {resp.status}')
                if resp.status == 200:
                    return await resp.json()
                else:
                    error = await resp.json()
                    return error['descriptions']

    async def request_download(self, user_id, folder_name: str = '', file: str = '', ext: str = ''):
        """get link to file or folder"""
        if users_db["user"].get(user_id).get("ya_upload_completed"):
            try:
                async with clientSession() as session:
                    async with session.get(f"{self.RESOURCES_URL}/download",
                                           params={
                                               'path': f"{self.ROOT_FOLDER}/{folder_name}/{file}{ext}"
                                           },
                                           headers={
                                               'Content-Type': 'application/json',
                                               'Accept': 'application/json',
                                               'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                           }) as resp:
                        print(f'user_id: {user_id}. Download folder: {self.ROOT_FOLDER}/{folder_name}.'
                              f' Response: {resp.status}')

            except KeyError as ke:
                print(f'download_file(user_id: {user_id}) KeyError' + str(ke.args))
                return f'download_file() KeyError {ke.args}'
            finally:
                href = await resp.json()
                if resp.status == 200:
                    return href['href']
                else:
                    return 'При получении ссылки на загрузку файла произошла ошибка'
        else:
            return f'download_file(user_id: {user_id}): ya_upload_completed: 0'

    # ----processing response from yandex disk api----

    # @profile(stream=fp, precision=4)
    async def request_upload_file(self, user_id: int, data: dict, folder_name: str, overwrite: bool = False):
        counter = 0
        subfolder_path = f'{self.ROOT_FOLDER}/{folder_name}'
        mininterval = len(data) / 1000
        async with clientSession() as session:
            async for url, ext in tqdm(data.items(), mininterval=mininterval, token=os.environ.get("BOT_TOKEN"),
                                       chat_id=user_id):
                try:
                    async with session.post(f"{self.RESOURCES_URL}/upload",
                                            params={
                                                'path': f'{subfolder_path}/{counter + 1}_file{ext}',
                                                'url': url,
                                                'overwrite': str(overwrite)
                                            },
                                            data=None,
                                            headers={
                                                'Content-Type': 'application/json',
                                                'Accept': 'application/json',
                                                'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                            }) as resp:
                        counter += 1
                        print(f" user_id: {user_id} | album: {subfolder_path} | status: {resp.status}")
                except ClientConnectorError:
                    await asyncio.sleep(0.07)
                    continue
            await session.close()
        users_db['user'].upsert(
            {
                "user_id": user_id,
                "total_number_uploaded_file":
                    users_db["user"].get(user_id).get("total_number_uploaded_file") + counter
            }, pk="user_id")
        print(f'uploaded {counter}')
        return counter

    # @profile(stream=fp, precision=4)
    async def create_directory(self, user_id, folder_name):
        users_db['user'].upsert(
            {
                "user_id": user_id,
                "ya_upload_completed": False,
            }, pk="user_id")
        start_create_dir = time.perf_counter()
        if await self.request_create_folder(user_id, self.ROOT_FOLDER):
            if await self.request_create_folder(user_id, f'{self.ROOT_FOLDER}/{folder_name}'):
                end_create_dir = time.perf_counter()
                print(f'user_id: {user_id}. Directory creation was done in '
                      f'{end_create_dir - start_create_dir:0.4f} seconds')
                return True

    async def upload_file(self, user_id: int, data: dict, folder_name: str, overwrite: bool = False):
        start = time.perf_counter()
        if await self.create_directory(user_id, folder_name):
            if len(data) <= 10:
                if (len(data) / await self.request_upload_file(user_id, data, folder_name, overwrite)) \
                        < 1.11111111111:
                    users_db["user"].upsert(
                        {
                            "user_id": user_id,
                            "ya_upload_completed": True,
                        }, pk='user_id')
            else:
                await self.multitask_post_requests(user_id, data, folder_name, overwrite)
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "ya_upload_completed": True,
                    }, pk='user_id')

        end = time.perf_counter()
        print(f'\nthe function upload_file(user_id: {user_id}) was completed in {end - start:0.4f} seconds')
