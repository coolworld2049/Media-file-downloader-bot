import requests

from data import ConfigStorage


class YandexDisk:
    def __init__(self):
        self.config = ConfigStorage.configParser
        self.URL = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.Y_API_TOKEN = self.config.get("YA_DISK_DATA", "Y_API_TOKEN")
        self.Y_APP_ID = self.config.get("YA_DISK_DATA", "Y_APP_ID")
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': f'OAuth {self.Y_API_TOKEN}'}
        self.authorized = False

    # authorization

    def auth_ya_disk_send_link(self):
        link = f'https://oauth.yandex.ru/authorize?response_type=token&client_id={self.Y_APP_ID}'
        return link

    def auth_ya_disk(self, ya_token: str):
        if len(ya_token) == 39:
            self.config.set("YA_DISK_DATA", "Y_API_TOKEN", ya_token)
            self.authorized = True
            return 'Вы успешно авторизовались в Яндекс диске!'
        else:
            self.authorized = False
            return 'Ошибка авторизации в Яндекс диске!'

    # actions with user disk

    def create_folder(self, path):
        requests.put(f'{self.URL}?path={path}', headers=self.headers)

    def upload_file(self, loadfile, savefile, replace=False):
        """Loading a file.
        savefile: Path to a file in Drive
        loadfile: Path to a file to be loaded
        replace: true or false Replace a file in Drive"""
        res = requests.get(f'{self.URL}/upload?path={savefile}&overwrite={replace}',
                           headers=self.headers).json()
        with open(loadfile, 'rb') as f:
            try:
                requests.put(res['href'], files={'file': f})
            except KeyError:
                print(res)
