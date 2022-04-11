import os
import time

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
    def auth(user_id, ya_token: str):
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

    def get_folders(self, user_id):
        meta_dir = requests.get(self.URL,
                                params={
                                    'path': f'{self.main_folder}/'
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    f'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                }).json()
        return meta_dir

    def create_folder(self, user_id, folder_name, attempts=10):
        resp = 0
        count = 0
        while resp != 201 or count < attempts:
            time.sleep(0.1)
            resp = requests.put(f'{self.URL}?',
                                params={
                                    'path': f'{folder_name}',
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                }).status_code
            print(f'Try create dir {folder_name} in cloud storage. Response code: {str(resp)}')
            if resp == 201:
                return True
            elif resp == 423:
                attempts += 1
                continue
            else:
                count += 1
                return False

    def delete_folder(self, user_id, folder_name, attempts=3):
        resp = 0
        count = 0
        while resp != (200 or 202 or 204) or (count < attempts):
            time.sleep(0.1)
            resp = requests.delete(f'{self.URL}?',
                                   params={
                                       'path': f'{folder_name}',
                                       'permanently': True
                                   },
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Accept': 'application/json',
                                       'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                   }).status_code
            print('Try delete dir ' + folder_name + ' in cloud storage. Response code: ' + str(resp))
            if resp == 200 or 202 or 204:
                return True
            elif resp == 423:
                attempts += 1
                continue
            else:
                count += 1
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

        subfolder_path = f'{self.main_folder}/{folder_name}'
        # rewriting main_folder in cloud
        if self.delete_folder(user_id, self.main_folder):
            if self.create_folder(user_id, self.main_folder):
                # rewriting subfolder in cloud
                subfolders_on_disk = self.get_folders(user_id)
                if len(subfolders_on_disk) != 3 and subfolders_on_disk['_embedded']['items'] != 0:
                    for a in subfolders_on_disk['_embedded']['items']:
                        if a['name'] == folder_name:
                            if self.delete_folder(user_id, subfolder_path):
                                break

        if self.create_folder(user_id, subfolder_path):
            status_code = 0
            counter = 0
            for i in tqdm(range(len(url_list)), token=os.environ.get("BOT_TOKEN"),
                          chat_id=user_id):
                if status_code == 202 or 200 or 0 and counter < 20:
                    try:
                        filename = str(counter + 1) + '_file'
                        time.sleep(0.02)
                        response = requests.post(f"{self.URL}/upload?",
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
                        print(f" Folder: {subfolder_path}. Response code: {status_code}")

                    except requests.exceptions.RequestException:
                        time.sleep(0.1)
                        continue
                else:
                    break

            users_db['user'].upsert(
                {
                    "user_id": user_id,
                    "number_uploaded_file": counter
                }, pk="user_id")

            if len(url_list) == users_db["user"].get(user_id).get("number_uploaded_file"):
                users_db["user"].upsert(
                    {
                        "user_id": user_id,
                        "ya_upload_completed": True,
                    }, pk='user_id')

            elif (len(url_list) - users_db["user"].get(user_id).get("number_uploaded_file")) < 20:
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
        print(f'\nthe function upload_file() was executed for {end - start:0.4f} seconds')
        print(f'uploaded {users_db["user"].get(user_id).get("number_uploaded_file")}')

    def get_link_file(self, user_id, folder_name: str):
        try:
            data = requests.get(f"{self.URL}/download?",
                                params={
                                    'path': f"{self.main_folder}/{folder_name}",
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {users_db["user"].get(user_id).get("y_api_token")}'
                                }).json()
            print(f'downloaded folder: {self.main_folder}/{folder_name}')
            return data['href']
        except KeyError as ke:
            print('get_link_file() KeyError' + str(ke.args))
            return 'get_link_file() KeyError' + str(ke.args)
