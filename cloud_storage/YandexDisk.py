import random
import time

import emoji
import requests

from data import ConfigStorage


class YandexDisk:
    def __init__(self):
        self.config = ConfigStorage.configParser
        self.path_to_config = ConfigStorage.path
        self.URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.user_authorized = False
        self.main_folder = 'Saved from tg'

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

    def get_folders_from_main_cat(self):
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
        print(f'Create dir {folder_name} in cloud storage. Response code: {str(resp)}')

        if resp == 201:
            return True
        else:
            return False

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
                               }).status_code
        print('Delete dir ' + folder_name + ' in cloud storage. Response code: ' + str(resp))

        if resp == 200 or 202 or 204:
            return True
        else:
            return False

    def upload_file(self, url_list: list, folder_name: str, extension: str = '.file', is_exist_extension: bool = True,
                    overwrite: bool = False):
        """if :param extension: does not exist then extract it from url_list"""

        start = time.perf_counter()

        subfolders_on_disk = self.get_folders_from_main_cat()
        subfolder_path = f'Saved from tg/{folder_name}'

        # rewriting folder in cloud
        if len(subfolders_on_disk) != 3 and subfolders_on_disk['_embedded']['items'] != 0:
            for a in subfolders_on_disk['_embedded']['items']:
                if a['name'] == folder_name:
                    time.sleep(0.3)
                    if self.delete_file(subfolder_path):
                        time.sleep(0.3)
                        self.create_file(subfolder_path)
                        break

        counter = 0
        except_message = ''

        self.create_file(self.main_folder)
        self.create_file(subfolder_path)

        self.upload_completed = False
        self.check_url_list.clear()

        self.config.read(self.path_to_config)
        if is_exist_extension:
            """exist only url"""
            status_code = 202
            for item in url_list:
                if status_code == 202 or 200:
                    time.sleep(0.2)
                    try:
                        filename = str(counter) + '_' + str(random.randint(1153, 546864))
                        status_code = requests.post(f"{self.URL}/upload?",
                                                    params={
                                                        'path': f'{subfolder_path}/{filename}.{extension}',
                                                        'url': item,
                                                        'overwrite': overwrite
                                                    },
                                                    headers={
                                                        'Content-Type': 'application/json',
                                                        'Accept': 'application/json',
                                                        'Authorization': f'OAuth {self.config["YA_DISK_DATA"]["y_api_token"]}'
                                                    }).status_code
                        if status_code == 202 or 200:
                            self.check_url_list.append(item)
                        counter += 1
                        print(f"upload file to yandex disk (folder: {subfolder_path}): "
                              f"№" + str(counter) + " response code " + f"{status_code}")

                    except requests.exceptions.RequestException:
                        time.sleep(0.1)
                        continue
                elif counter > 10:
                    break
        else:
            """exist url and file extension"""
            status_code = 202
            for i in range(len(url_list)):
                if status_code == 202 or 200:
                    time.sleep(0.2)
                    try:
                        filename = str(counter) + '_' + str(random.randint(1153, 546864))
                        status_code = requests.post(f"{self.URL}/upload?",
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
                        if status_code == 202 or 200:
                            self.check_url_list.append(url_list[i][0])
                        counter += 1
                        print(f"upload file to yandex disk (folder: {subfolder_path}):"
                              f" №" + str(counter) + " response code " + f"{status_code}")

                    except requests.exceptions.RequestException:
                        time.sleep(0.1)
                        continue
                elif counter > 10:
                    break

        number_uploaded_files = len(self.check_url_list)

        end = time.perf_counter()
        print(f'the function upload_file() was executed for {end - start:0.4f} seconds')
        print(f'uploaded {len(self.check_url_list)} files to Yandex Disk')

        if len(self.check_url_list) == len(url_list):
            self.upload_completed = True
            return emoji.emojize(f":check_mark: Файлы загружены в папку на Яндекс диске\n"
                                 f"                      '{subfolder_path}'\n"
                                 f":check_mark: Количество загруженных файлов: {number_uploaded_files}")
        else:
            self.upload_completed = False
            return emoji.emojize(f":cross_mark_button: При загрузке файлов на облако произошла"
                                 f" ошибка {except_message}."
                                 f" Загружено {number_uploaded_files} файлов")

    def download_file(self, folder_name: str):
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
