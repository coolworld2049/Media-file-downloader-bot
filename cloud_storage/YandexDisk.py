import asyncio
import os
import time
from abc import abstractmethod
from asyncio import gather

from aiohttp import ClientSession as clientSession, ClientConnectorError
from icecream import ic
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

    # ------------------------TESTED------------------------

    @staticmethod
    # @profile(stream=fp, precision=4)
    async def upload_request_worker(counter: int, client_session: clientSession(), url: str, params: dict, data: str,
                                    headers: dict):
        start = time.time()
        async with client_session as session:
            async with session.post(url=url, params=params, data=data, headers=headers) as response:
                end = time.time()
                completed_id = f'Task {counter - 1} completed in {end - start:0.4f} seconds'
                resp_code = f'Response code: {response.status}'
                ic((completed_id, url, params, data, headers, resp_code, client_session))
                await session.close()
                return await response.json()

    @staticmethod
    async def wrapper(delay, coro):
        await asyncio.sleep(delay)
        return await coro

    @staticmethod
    # @profile(stream=fp, precision=4)
    async def upload_request_controller(list_of_chunks: list):
        tasks = [
            asyncio.create_task(YandexDisk().upload_request_worker(
                index,
                clientSession(),
                list_of_chunks[index]['url'],
                list_of_chunks[index]['params'],
                list_of_chunks[index]['data'],
                list_of_chunks[index]['headers']))
            for index in range(len(list_of_chunks))
        ]
        result = [await gather(YandexDisk().wrapper(0.1, tasks[task]))
                  for task in range(len(tasks))]
        """result2 = [await gather(*tasks, return_exceptions=True)]
        for res in result2:
            if isinstance(res, BaseException):
                print(f'BaseException: {res}')
                ic(res)"""
        return result

    @staticmethod
    # @profile(stream=fp, precision=4)
    async def get_operation_status(user_id, operation_id: str | list):
        if isinstance(operation_id, str):
            await asyncio.sleep(0.02)
            async with clientSession() as session:
                async with session.get(f'https://cloud-api.yandex.net/v1/disk/operations',
                                       params={
                                           'operation_id': operation_id
                                       },
                                       headers={
                                           'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                       }) as resp:
                    return await resp.json()

        elif isinstance(operation_id, list):
            async with clientSession() as session:
                for res in operation_id:
                    op_id_href: str = res[0]['href']
                    op_id = op_id_href.split('/')
                    async with session.get(f'https://cloud-api.yandex.net/v1/disk/operations',
                                           params={
                                               'operation_id': op_id[-1]
                                           },
                                           headers={
                                               'Content-Type': 'application/json',
                                               'Accept': 'application/json',
                                               'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                           }) as resp:
                        return await resp.json()

    # @profile(stream=fp, precision=4)
    async def multiple_post_requests(self, user_id: int, cs: clientSession(), url: str, ext: str, counter: int,
                                     folder_name: str, overwrite: bool = False):
        subfolder_path = f'{self.ROOT_FOLDER}/{folder_name}'
        async with cs as session:
            while True:
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
                        print(f" album: {subfolder_path} | status: {resp.status}")
                except ClientConnectorError:
                    print('multiple_post_requests ClientConnectorError')
                    await asyncio.sleep(0.05)
                    continue
                finally:
                    await session.close()

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

        chunk_size = len(requests_dict)
        requests_list = [value for key, value in requests_dict.items()]
        list_of_chunks = [requests_list[i:i + chunk_size]
                          for i in range(0, len(requests_list), chunk_size)]
        if len(requests_dict) >= chunk_size:
            result = []
            for chunk in tqdm(range(len(list_of_chunks)), token=os.environ.get("BOT_TOKEN"),
                              chat_id=user_id):
                result.append(await YandexDisk().upload_request_controller(list_of_chunks[chunk]))
                status = [await YandexDisk().get_operation_status(user_id, result[chunk][i][0]['href'])
                          for i in range(len(result[chunk]))]
                ic(status)
            ic(result)

        else:
            result = [await YandexDisk().upload_request_controller(requests_list)]
            ic(result)
            status = [await YandexDisk().get_operation_status(user_id, result[0][i][0]['href'])
                      for i in range(len(result[0]))]
            ic(status)

    # ------------------------WORKING------------------------

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

    # ----processing response from vk api----

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
            # await YandexDisk().multitask_post_requests(user_id, data, folder_name, overwrite)
            """counter = 0
            for url, ext in tqdm(data.items(), token=os.environ.get("BOT_TOKEN"), chat_id=user_id):
                await asyncio.gather(YandexDisk().multiple_post_requests(user_id,
                                                                         clientSession(),
                                                                         url, ext,
                                                                         counter,
                                                                         folder_name,
                                                                         overwrite))
                counter += 1
            users_db['user'].upsert(
            {
                "user_id": user_id,
                "total_number_uploaded_file": 
                    users_db["user"].get(user_id).get("total_number_uploaded_file") + counter
            }, pk="user_id")"""

            if (len(data) / await self.request_upload_file(user_id, data, folder_name, overwrite)) \
                    < 1.11111111111:
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "ya_upload_completed": True,
                    }, pk='user_id')
        end = time.perf_counter()
        print(f'\nthe function upload_file(user_id: {user_id}) was completed in {end - start:0.4f} seconds')
