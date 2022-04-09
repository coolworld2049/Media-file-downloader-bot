import os
import random
import time

import requests
from tqdm.contrib.telegram import tqdm

from data import config


class YandexDisk:
    def __init__(self):
        self.config = config.configParser
        self.path_to_config = config.path
        self.URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.user_authorized = False
        self.main_folder = 'Saved from tg'
        self.bot_chat_id = ''
        self.check_url_list = 0
        self.upload_completed = False

    # authorization

    def send_link(self):
        self.config.read(self.path_to_config)

        link = f'https://oauth.yandex.ru/authorize?response_type=token' \
               f'&client_id={self.config["YA_DISK_DATA"]["y_app_id"]}'
        return link

    def auth(self, ya_token: str):
        if len(ya_token) == 39:
            self.config.read(self.path_to_config)
            self.config.set("YA_DISK_DATA", "y_api_token", ya_token)
            self.config.write(open(self.path_to_config, "w"))

            self.user_authorized = True
            return 'Вы успешно авторизовались в Яндекс диске!'
        else:
            self.user_authorized = False
            return 'Ошибка авторизации в Яндекс диске!'

    # actions with user disk

    def get_folders(self):
        self.config.read(self.path_to_config)

        meta_dir = requests.get(f'{self.URL}?',
                                params={
                                    'path': f'{self.main_folder}/'
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                }).json()
        return meta_dir

    def create_folder(self, folder_name):
        resp = requests.put(f'{self.URL}?',
                            params={
                                'path': f'{folder_name}',
                            },
                            headers={
                                'Content-Type': 'application/json',
                                'Accept': 'application/json',
                                'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                            }).status_code
        print(f'Create dir {self.main_folder}/{folder_name} in cloud storage. Response code: {str(resp)}')

        if resp == 201:
            return True
        else:
            return False

    def delete_folder(self, folder_name):
        self.config.read(self.path_to_config)

        resp = requests.delete(f'{self.URL}?',
                               params={
                                   'path': f'{folder_name}',
                                   'permanently': True
                               },
                               headers={
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json',
                                   'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                               }).status_code
        print('Delete dir ' + folder_name + ' in cloud storage. Response code: ' + str(resp))

        if resp == 200 or 202 or 204:
            return True
        else:
            return False

    def upload_file(self, url_list: list, folder_name: str, overwrite: bool = False):
        start = time.perf_counter()

        self.config.read(self.path_to_config)

        subfolders_on_disk = self.get_folders()
        subfolder_path = f'Saved from tg/{folder_name}'
        # rewriting folder in cloud
        if len(subfolders_on_disk) != 3 and subfolders_on_disk['_embedded']['items'] != 0:
            for a in subfolders_on_disk['_embedded']['items']:
                if a['name'] == folder_name:
                    self.delete_folder(subfolder_path)

        time.sleep(0.1)
        self.create_folder(self.main_folder)
        time.sleep(0.1)
        self.create_folder(subfolder_path)

        self.upload_completed = False
        self.check_url_list = 0

        status_code = 0
        counter = 0

        for i in tqdm(range(len(url_list)), token=os.environ.get("BOT_TOKEN"), chat_id=self.bot_chat_id):
            if status_code == 202 or 200 or 0 and counter < 20:
                try:
                    filename = str(counter + 1) + '_' + str(random.randint(1153, 546864))
                    time.sleep(0.1)
                    response = requests.post(f"{self.URL}/upload?",
                                             params={
                                                 'path': f'{subfolder_path}/{filename}.{url_list[i][1]}',
                                                 'url': url_list[i][0],
                                                 'overwrite': overwrite
                                             },
                                             headers={
                                                 'Content-Type': 'application/json',
                                                 'Accept': 'application/json',
                                                 'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                             }).status_code
                    status_code = response
                    self.check_url_list += 1
                    counter += 1
                    print(f" Folder: {subfolder_path}. Response code: {status_code}")

                except requests.exceptions.RequestException:
                    time.sleep(0.1)
                    continue
            else:
                break

        end = time.perf_counter()
        print(f'\nthe function upload_file() was executed for {end - start:0.4f} seconds')
        print(f'uploaded {self.check_url_list} files to Yandex Disk')

        if len(url_list) == self.check_url_list:
            self.upload_completed = True

        elif (len(url_list) - self.check_url_list) < 20:
            self.upload_completed = True
        else:
            self.upload_completed = False

    def get_link_file(self, folder_name: str):
        try:
            data = requests.get(f"{self.URL}/download?",
                                params={
                                    'path': f"{self.main_folder}/{folder_name}",
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                }).json()
            print(f'downloaded folder: {self.main_folder}/{folder_name}')
            return data['href']
        except KeyError as ke:
            print('download_file()' + str(ke.args))
            return ke.args
