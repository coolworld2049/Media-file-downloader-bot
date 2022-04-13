import asyncio
import os
import time

import aiohttp
import requests
from tqdm.contrib.telegram import tqdm

from db.database import users_db


class YandexDisk:
    def __init__(self):
        self.app_id = '131f4986553d493184f6a5e5af832174'
        self.URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.main_folder = 'Saved from tg'

    # authorization

    def send_link(self):

        link = f'https://oauth.yandex.ru/authorize?response_type=token' \
               f'&client_id={self.app_id}'
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
        """'path': f'{self.main_folder}/'"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL,
                                   params={
                                       'path': f'{self.main_folder}/'
                                   },
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Accept': 'application/json',
                                       f'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                   }) as resp:
                return await resp.json()

    async def create_folder(self, user_id, folder_name, attempts=3):
        resp = 0
        count = 0
        while resp != 201 or (count < attempts):
            await asyncio.sleep(0.1)
            resp = requests.put(f'{self.URL}',
                                params={
                                    'path': f'{folder_name}',
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                }).status_code
            count += 1
            print(f'Try create dir "{folder_name}" in cloud storage. Response code: {str(resp)}')
            if resp == 201 or 409:
                return True
            if resp == 423:
                attempts += 1
                continue
            else:
                return False

    async def delete_folder(self, user_id, folder_name, attempts=3):
        resp = 0
        count = 0
        while resp != (200 or 202 or 204) or (count < attempts):
            await asyncio.sleep(0.1)
            resp = requests.delete(f'{self.URL}',
                                   params={
                                       'path': f'{folder_name}',
                                       'permanently': True
                                   },
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Accept': 'application/json',
                                       'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                   }).status_code
            count += 1
            print(f'Try delete dir "{folder_name}" in cloud storage. Response code: {resp}')
            if resp == 200 or 202 or 204:
                return True
            if resp == 423:
                attempts += 1
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
        subfolder_path = f'{self.main_folder}/{folder_name}'
        # create dir main_folder in cloud if not exist
        if await self.create_folder(user_id, self.main_folder):
            # get all subfolders in main_folder
            subfolders_on_disk = await self.get_folders(user_id)
            if len(subfolders_on_disk) != 3 and subfolders_on_disk['_embedded']['items'] != 0:
                for a in subfolders_on_disk['_embedded']['items']:
                    # rewrite exist subfolder in main_folder
                    if a['name'] == folder_name:
                        if await self.delete_folder(user_id, subfolder_path):
                            if await self.create_folder(user_id, subfolder_path):
                                break
        end_dir = time.perf_counter()
        print(f'Directory creation was done in {end_dir - start_dir:0.4f} seconds')

        if await self.create_folder(user_id, subfolder_path):
            status_code = 0
            counter = 0
            for i in tqdm(range(len(url_list)), token=os.environ.get("BOT_TOKEN"),
                          chat_id=user_id):
                if status_code == 202 or 200 or 0 and counter < 20:
                    try:
                        filename = str(counter + 1) + '_file'
                        await asyncio.sleep(0.02)
                        response = requests.post(f"{self.URL}/upload",
                                                 params={
                                                     'path': f'{subfolder_path}/{filename}{url_list[i][1]}',
                                                     'url': url_list[i][0],
                                                     'overwrite': overwrite
                                                 },
                                                 headers={
                                                     'Content-Type': 'application/json',
                                                     'Accept': 'application/json',
                                                     'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                                 }).status_code

                        status_code = response
                        counter += 1
                        print(f" album: {folder_name} | status: {status_code}")

                    except requests.exceptions.RequestException:
                        await asyncio.sleep(0.07)
                        continue
                else:
                    try:
                        filename = str(counter + 1) + '_file'
                        await asyncio.sleep(0.02)
                        response = requests.post(f"{self.URL}/upload",
                                                 params={
                                                     'path': f'{subfolder_path}/{filename}{url_list[i-1][1]}',
                                                     'url': url_list[i-1][0],
                                                     'overwrite': overwrite
                                                 },
                                                 headers={
                                                     'Content-Type': 'application/json',
                                                     'Accept': 'application/json',
                                                     'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                                 }).status_code

                        status_code = response
                        counter += 1
                        print(f" album: {folder_name} | status: {status_code}")

                    except requests.exceptions.RequestException:
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
        print(f'\nthe function upload_file() was completed in {end - start:0.4f} seconds')
        print(f'uploaded {users_db["user"].get(user_id).get("number_uploaded_file")}')

    async def get_link_file(self, user_id, folder_name: str):
        if users_db["user"].get(user_id).get("ya_upload_completed"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.URL}/download",
                                           params={
                                               'path': f"{self.main_folder}/{folder_name}"
                                           },
                                           headers={
                                               'Content-Type': 'application/json',
                                               'Accept': 'application/json',
                                               'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                           }) as resp:
                        print(f'downloaded folder: {self.main_folder}/{folder_name}')
                        return await resp.json()

            except KeyError as ke:
                print('get_link_file() KeyError' + str(ke.args))
                return f'get_link_file() KeyError {ke.args}'
        else:
            return 'get_link_file(): ya_upload_completed: 0'
