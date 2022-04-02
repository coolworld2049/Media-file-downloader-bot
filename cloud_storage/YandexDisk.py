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
        self.check_url_list = []
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

    def create_file(self, folder_name):
        resp = requests.put(f'{self.URL}?',
                            params={
                                'path': f'{folder_name}',
                            },
                            headers={
                                'Content-Type': 'application/json',
                                'Accept': 'application/json',
                                'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                            }).status_code
        print('Create dir ' + folder_name + ' in cloud storage. Response code: ' + str(resp))

    def delete_file(self, folder_name):
        self.config.read(self.path_to_config)

        resp = requests.delete(f'{self.URL}?',
                               params={
                                   'path': f'{folder_name}'
                               },
                               headers={
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json',
                                   'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                               })
        print('Delete dir ' + folder_name + ' in cloud storage. Response code: ' + str(resp))

    def upload_file(self, url_list: list, folder_name: str, extension: str):
        """path = folder_name/filename.ext"""
        self.config.read(self.path_to_config)

        """# creating file
        meta_dir = requests.get(f'{self.URL}?',
                                params={
                                    'path': '/'
                                },
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                }).json()
        # creating folder list
        for el in meta_dir['_embedded']['items']:
            if folder_name == el['name']:
                self.delete_file(folder_name)
                time.sleep(0.3)
                self.create_file(folder_name)
            else:
                self.create_file(folder_name)
"""
        self.create_file(folder_name)
        time.sleep(0.3)
        counter = 0
        except_message = ''
        try:
            for item in url_list:
                filename = str(random.randint(1153, 546864))
                try:
                    time.sleep(0.3)
                    response = requests.post(f"{self.URL}/upload?",
                                             params={
                                                 'url': item,
                                                 'path': f'{folder_name}/{filename}.{extension}',
                                             },
                                             headers={
                                                 'Content-Type': 'application/json',
                                                 'Accept': 'application/json',
                                                 'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                             }).status_code
                    if response == 202 or 200:
                        self.check_url_list.append(item)
                    counter += 1
                    print("upload file to yandex disk: №" + str(counter) + " response code " + f"{response}")

                except requests.exceptions.RequestException:
                    time.sleep(0.3)
                    continue

        except KeyError as ke:
            except_message = ke.args
            print(ke.args)

        except Exception as e:
            except_message = e.args
            print(e.args)

        number_uploaded_files = len(self.check_url_list)

        if len(self.check_url_list) == len(url_list):
            self.upload_completed = True
            return f'{number_uploaded_files} файлов загружено на облако'
        else:
            self.upload_completed = False
            return f'При загрузке файлов на облако произошла ошибка {except_message}.' \
                   f' Загружено {number_uploaded_files} файлов'
