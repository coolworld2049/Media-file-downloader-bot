import random
import time

import requests

from data import ConfigStorage


class YandexDisk:
    def __init__(self):
        self.config = ConfigStorage.configParser
        self.path_to_config = ConfigStorage.path
        self.URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.user_authorized = False
        self.url_list = []
        self.upload_completed = False

    # authorization

    def auth_ya_disk_send_link(self):
        self.config.read(self.path_to_config)

        link = f'https://oauth.yandex.ru/authorize?response_type=token' \
               f'&client_id={self.config["YA_DISK_DATA"]["y_app_id"]}'
        return link

    def auth_ya_disk(self, ya_token: str):
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

    def create_folder(self, folder_name: str):
        self.config.read(self.path_to_config)

        requests.put(f'{self.URL}?',
                     params={
                         'path': f'{folder_name}',
                     },
                     headers={
                         'Content-Type': 'application/json',
                         'Accept': 'application/json',
                         'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                     })

    def upload_file(self, url: str, folder_name: str, extension: str, replace=False):
        """path = /folder_name/filename.ext"""
        self.config.read(self.path_to_config)

        filename = str(random.randint(1153, 546864))
        count = len(self.url_list)
        counter = 1
        try:
            time.sleep(0.1)
            res = requests.post(f"{self.URL}/upload?",
                                params={
                                    'url': url,
                                    'path': f'{folder_name}/{filename}.{extension}',
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                }).status_code
            self.url_list.append(url)
            counter += 1
            print("photo №" + str(counter) + " code" + str(res))

        except requests.exceptions as re:
            print(re.args)

        except Exception as e:
            print(e.args)

        """if count == counter:
            self.upload_completed = True
            return 'Файлы загружены на диск'
        else:
            self.upload_completed = False
            return 'При загрузке файлов произошла ошибка'"""


