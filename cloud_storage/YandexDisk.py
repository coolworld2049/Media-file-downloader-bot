import asyncio
import os
import time
from abc import abstractmethod
from typing import TextIO

import nest_asyncio
from aiohttp import ClientSession as clientSession, ClientConnectorError
from tqdm.contrib.telegram import tqdm

from core import users_db, logger


class YandexDisk:
    def __init__(self):
        self.__RESOURCES_URL__ = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.__ROOT_FOLDER__ = 'Saved from tg'

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
        if len(ya_token) == 7:
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
        else:
            return f'Вы ввели некорректную информацию'

    @staticmethod
    async def __request_upload_worker(url: str, params: dict, data: str, headers: dict):
        async with clientSession() as session:
            async with session.post(url=url, params=params, data=data, headers=headers):
                await session.close()

    @staticmethod
    async def __wrapper(delay, coro):
        await asyncio.sleep(delay)
        return await coro

    async def __multitask_post_requests(self, user_id: int, data: dict, folder_name: str, overwrite: bool = False):
        counter = 0
        subfolder_path = f'{self.__ROOT_FOLDER__}/{folder_name}'
        requests_dict = {}
        for url, ext in data.items():
            requests_dict[counter] = {
                'url': f"{self.__RESOURCES_URL__}/upload",
                'params': {
                    'path': f'{subfolder_path}/{counter + 1}_file{ext}',
                    'url': url,
                    'fields': 'href',
                    'overwrite': f'{overwrite}'},
                'data': None,
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'}
            }
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
                        self.__wrapper(0.03, self.__request_upload_worker(ch_items['url'],
                                                                          ch_items['params'],
                                                                          ch_items['data'],
                                                                          ch_items['headers']))))
                await asyncio.sleep(1.1)
                for k in range(len(tasks)):
                    await tasks[i]
                    logger.info(f'user_id {user_id}. Task {i} await: {tasks[i]}')

    # ----yandex disk api requests----

    async def __request_create_folder(self, user_id, folder_name, recreate_folder):
        status = 0
        count = 0
        while status != 201 or status not in (400, 401, 503, 507):
            try:
                async with clientSession() as session:
                    async with session.put(f'{self.__RESOURCES_URL__}?',
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
                        logger.info(f'user_id: {user_id}. Try create dir "{folder_name}" in cloud storage.'
                                    f' Response code: {str(resp.status)}. Message: {await resp.json()}')
                        match status:
                            case 201:
                                return True
                            case 423:
                                continue
                            case 429:
                                await asyncio.sleep(0.05)
                            case 404:
                                await self.__request_create_folder(user_id, self.__ROOT_FOLDER__,
                                                                   recreate_folder)
                            case 409:
                                if folder_name == self.__ROOT_FOLDER__:
                                    return True
                                elif not recreate_folder:
                                    return True
                                else:
                                    await self.__request_delete_folder(user_id, folder_name)
                            case _:
                                return False
            except ClientConnectorError as cce:
                logger.info(f'__request_create_folder(user_id: {user_id}) ClientConnectorError' + str(cce.args))
                await asyncio.sleep(0.1)
                continue

    async def __request_delete_folder(self, user_id, folder_name):
        status = 0
        count = 0
        while status != 200 or 202 or 204:
            try:
                await asyncio.sleep(0.05)
                async with clientSession() as session:
                    async with session.delete(f'{self.__RESOURCES_URL__}?',
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
                        logger.info(f'user_id: {user_id}. Try delete dir "{folder_name}" in cloud storage.'
                                    f' Response code: {str(resp.status)}. Message: {await resp.json()}')
                match status:
                    case 200 | 202 | 204:
                        return True
                    case 423:
                        continue
                    case _:
                        return False
            except ClientConnectorError as cce:
                logger.info(f'__request_delete_folder(user_id: {user_id}) ClientConnectorError' + str(cce.args))
                await asyncio.sleep(0.1)
                continue

    async def request_publish(self, user_id, folder_name: str):
        if users_db["user"].get(user_id).get("ya_upload_completed"):
            try:
                async with clientSession() as session:
                    async with session.put(f"{self.__RESOURCES_URL__}/publish",
                                           params={
                                               'path': f"{self.__ROOT_FOLDER__}/{folder_name}"
                                           },
                                           data=None,
                                           headers={
                                               'Content-Type': 'application/json',
                                               'Accept': 'application/json',
                                               'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                           }) as put_resp:
                        logger.info(f'user_id: {user_id}. Publish folder: {self.__ROOT_FOLDER__}/{folder_name}.'
                                    f' Response: {put_resp.status}')

            except KeyError as ke:
                logger.info(f'get_link_file(user_id: {user_id}) KeyError' + str(ke.args))
                return f'get_link_file() KeyError {ke.args}'
            finally:
                published = await self.__request_public(user_id, folder_name)
                if published:
                    for item in published['items']:
                        if item['name'] == folder_name:
                            return item['public_url']
                else:
                    return 'При получении ссылки на опубликованный ресурс произошла ошибка'
        else:
            return f'get_link_file(user_id: {user_id}): ya_upload_completed: 0'

    async def __request_public(self, user_id, folder_name: str = ''):
        """get_published_file"""
        async with clientSession() as session:
            async with session.get(f"{self.__RESOURCES_URL__}/public",
                                   params={
                                       'path': f"{self.__ROOT_FOLDER__}/{folder_name}",
                                       'type': 'dir',
                                       'preview_crop': 'true'
                                   },
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Accept': 'application/json',
                                       'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                   }) as resp:
                logger.info(f'user_id: {user_id}. Get published folder: {self.__ROOT_FOLDER__}/{folder_name}.'
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
                    async with session.get(f"{self.__RESOURCES_URL__}/download",
                                           params={
                                               'path': f"{self.__ROOT_FOLDER__}/{folder_name}/{file}{ext}"
                                           },
                                           headers={
                                               'Content-Type': 'application/json',
                                               'Accept': 'application/json',
                                               'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                           }) as resp:
                        logger.info(f'user_id: {user_id}. Download folder: {self.__ROOT_FOLDER__}/{folder_name}.'
                                    f' Response: {resp.status}')

            except KeyError as ke:
                logger.info(f'download_file(user_id: {user_id}) KeyError' + str(ke.args))
                return f'download_file() KeyError {ke.args}'
            except ClientConnectorError as cce:
                logger.info(f'download_file(user_id: {user_id}) ClientConnectorError' + str(cce.args))
                return f'download_file() ClientConnectorError {cce.args}'
            finally:
                href = await resp.json()
                if resp.status == 200:
                    return href['href']
                else:
                    return 'При получении ссылки на загрузку файла произошла ошибка'
        else:
            return f'download_file(user_id: {user_id}): ya_upload_completed: 0'

    # ----processing response from yandex disk api----

    async def request_upload_file(self, user_id: int, data: dict, folder_name: str, overwrite: bool = False):
        counter = 0
        subfolder_path = f'{self.__ROOT_FOLDER__}/{folder_name}'
        mininterval = len(data) / 1000
        async with clientSession() as session:
            async for url, ext in tqdm(data.items(), mininterval=mininterval, token=os.environ.get("BOT_TOKEN"),
                                       chat_id=user_id):
                try:
                    async with session.post(f"{self.__RESOURCES_URL__}/upload",
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
                        logger.info(f" user_id: {user_id} | album: {subfolder_path} | status: {resp.status}")
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
        logger.info(f'uploaded {counter}')
        return counter

    async def __create_directory(self, user_id, folder_name, recreate_folder):
        users_db['user'].upsert(
            {
                "user_id": user_id,
                "ya_upload_completed": False,
            }, pk="user_id")
        start_create_dir = time.perf_counter()
        if await self.__request_create_folder(user_id, self.__ROOT_FOLDER__, recreate_folder=False):
            if await self.__request_create_folder(user_id, f'{self.__ROOT_FOLDER__}/{folder_name}',
                                                  recreate_folder):
                end_create_dir = time.perf_counter()
                logger.info(f'user_id: {user_id}. Directory creation was done in '
                            f'{end_create_dir - start_create_dir:0.4f} seconds')
                return True

    async def upload_file(self, user_id: int, data: dict | TextIO, folder_name: str, overwrite: bool = False,
                          recreate_folder: bool = True):
        start = time.perf_counter()
        if isinstance(data, dict):
            if await self.__create_directory(user_id, folder_name, recreate_folder):
                if (1 <= len(data) <= 10) and (len(data) / await self.request_upload_file(
                        user_id, data, folder_name, overwrite)) < 1.11111111111:
                    users_db["user"].upsert(
                        {
                            "user_id": user_id,
                            "ya_upload_completed": True,
                        }, pk='user_id')
                else:
                    await self.__multitask_post_requests(user_id, data, folder_name, overwrite)
                    users_db["user"].upsert(
                        {
                            "user_id": user_id,
                            "ya_upload_completed": True,
                        }, pk='user_id')
        elif isinstance(data, TextIO):
            pass

        end = time.perf_counter()
        logger.info(f'upload_file(user_id: {user_id}) was completed in {end - start:0.4f} seconds')
