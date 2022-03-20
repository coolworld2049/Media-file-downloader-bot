import configparser
import json
import os
import time
import random
import requests


def get_scopes():
    config = configparser.ConfigParser()
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/apps.getScopes", params={
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'owner_id': 'user',
        'v': 5.131
    })
    data = json.loads(api.text)
    i = 0
    while i <= data["response"]["count"]:
        for names in data["response"]["items"]:
            scopes_list: list = names["items"]["name"]
            scopes_list.append(',')
            i += 1
    return scopes_list


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


def docs_get(count=0):
    config = configparser.ConfigParser()
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/docs.get", params={
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'count': count,
        'v': 5.131
    })

    with open("docs data.json", "w") as write_file:
        json.dump(json.loads(api.text), write_file, indent=4)
        write_file.close()

    return json.loads(api.text)


def save_photo():
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


def save_docs():
    data = docs_get()
    count = 100
    items_count = data["response"]["count"]
    i = 0
    while i <= data["response"]["count"]:
        if i != 0:
            data = docs_get(count=count)

        for docs in data["response"]["items"]:
            docs_url = docs["url"]
            filename = random.randint(1153, 5468645)
            try:
                time.sleep(0.1)
                api = requests.get(docs_url)
                with open(f"Saved docs/{filename}." + docs["ext"], "wb") as write_file:
                    write_file.write(api.content)
                i += 1
                print(f"{i}/{items_count}")
            except requests.exceptions:
                print("Server connection")
                time.sleep(0.5)
                continue


def start(scope_type: str):
    config = configparser.ConfigParser()

    if scope_type == 'photos':
        while True:
            what_download = input("\nEnter your user_id:\n")
            if not what_download.isnumeric():
                print("You didn't enter a number. Try again:")
            elif not 100000000 <= int(what_download) <= 999999999:
                print("Your number is out of range. Try again")
            else:
                break
        config.set("VK_ACC_DATA", "vk_user_id", what_download)
        config.write(open("config.ini", "w"))
        time.sleep(0.5)
        save_photo()  # def
        path_data_photo = os.path.abspath("Saved data/Saved docs")
        return f"\nLoading is complete. " \
               f"The downloaded files are located at {path_data_photo}"

    elif scope_type == 'docs':
        save_docs()  # def
        path_data_docs = os.path.abspath("Saved data/Saved docs")
        return f"\nLoading is complete. " \
               f"The downloaded files are located at {path_data_docs}"
