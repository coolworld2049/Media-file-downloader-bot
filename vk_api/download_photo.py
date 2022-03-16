import configparser
import json
import time
import random
import requests


def get_all_photos(offset=0, count=0):
    config = configparser.ConfigParser()
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/photos.getAll", params={
        'owner_id': int(config['VK_ACC_DATA']['vk_user_id']),
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'offset': offset,
        'count_photos': count,
        'photo_sizes': 0,
        'v': 5.131
    })

    with open("photos data", "w") as write_file:
        json.dump(json.loads(api.text)["response"], write_file, indent=4)
        write_file.close()
    return json.loads(api.text)


def save_photo():
    try:
        data = get_all_photos()
        count = 1
        items_count = data["response"]["count"]
        i = 0
        while i <= data["response"]["count"]:
            if i != 0:
                data = get_all_photos(offset=i, count=count)

            for photos in data["response"]["items"]:
                photo_url = photos["sizes"][-1]["url"]
                filename = random.randint(1153, 546864)
                try:
                    time.sleep(0.1)
                    api = requests.get(photo_url)
                    with open(f"Saved photos/{filename}" + ".jpg", "wb") as write_file:
                        write_file.write(api.content)
                    i += 1
                    print(f"{i}/{items_count}")
                except requests.exceptions:
                    time.sleep(0.5)
                    continue
    except KeyError:
        from main import rm_temp_files
        rm_temp_files()
