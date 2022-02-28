import configparser
import json
import random
import time
import requests
import configparser
from multiprocessing import Process

config = configparser.ConfigParser()
config.read('config.ini')

VK_APP_ID = config['VK_ACC_DATA']['VK_APP_ID']
VK_TOKEN = config['VK_ACC_DATA']['VK_TOKEN']
VK_ALBUM_ID = config['VK_ACC_DATA']['VK_ALBUM_ID']


def get_photo_data(offset=0, count=100):
    api = requests.get("https://api.vk.com/method/photos.getAll", params={
        'owner_id': VK_ALBUM_ID,
        'access_token': VK_TOKEN,
        'offset': offset,
        'count_photos': count,
        'photo_sizes': 0,
        'v': 5.131
    })
    #    with open("photos data", "w") as write_file:
    #        json.dump(json.loads(api.text)["response"], write_file, indent=4)

    return json.loads(api.text)


def download_photo():
    data = get_photo_data()
    count = 100
    i = 0
    while i <= data["response"]["count"]:
        if i != 0:
            data = get_photo_data(offset=i, count=count)

        for photos in data["response"]["items"]:
            photo_url = photos["sizes"][-1]["url"]
            filename = random.randint(15487, 546864)
            time.sleep(0.1)
            api = requests.get(photo_url)

            with open(f"Saved photo/{filename}" + ".jpg", "wb") as write_file:
                write_file.write(api.content)
        i += count
        print(i)


if __name__ == "__main__":
    download_photo()
