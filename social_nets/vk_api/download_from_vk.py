import json
import os
import time
import random
import requests

from social_nets.vk_api.auth import config


def get_scopes():
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


def get_by_id(photo_id):
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/photos.getById", params={
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'photos': config['VK_ACC_DATA']['user_id'] + "_" + photo_id,
        'v': 5.131
    })
    return json.loads(api.text)


def get_albums():
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/photos.getAlbums", params={
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'v': 5.131
    })
    return json.loads(api.text)


def get_albums_count():
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/photos.getAlbumsCount", params={
        'user_id': int(config['VK_ACC_DATA']['vk_user_id']),
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'v': 5.131
    })
    return json.loads(api.text)['response']


def get_all_photos(offset=0, count=0):
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/photos.getAll", params={
        'owner_id': int(config['VK_ACC_DATA']['vk_user_id']),
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'offset': offset,
        'count_photos': count,
        'photo_sizes': 0,
        'v': 5.131
    })
    return json.loads(api.text)


def docs_get(count=0):
    config.read('config.ini')

    api = requests.get("https://api.vk.com/method/docs.get", params={
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'count': count,
        'v': 5.131
    })
    return json.loads(api.text)


def eliminate_repetitions(list1):
    list2 = []
    for item in list1:
        if item not in list2:
            list2.append(item)
    return list2


def albums_with_photos():
    # получаем список id альбомов из списка всех фотографий - getAll
    global album_id, final_album, album_and_photos
    album_and_photos = []
    photos = get_all_photos()
    c = 0
    while c <= photos["response"]["count"]:
        album_and_photos.append(photos["response"]["items"][c]["album_id"])
        c += 1
    album_and_photos = eliminate_repetitions(album_and_photos)

    # получаем список id всех альбомов аккаунта - getAlbums
    albums_list = get_albums()
    v = 0
    while v <= albums_list["response"]["count"]:
        album_id.append(albums_list["response"]["items"][v]["id"])
        v += 1
    album_and_photos = eliminate_repetitions(album_id)

    # сопостовляем каждому альбому его фотографии
    k = 0
    m = 0
    while k <= len(album_id):
        while m <= len(album_and_photos):
            if album_id[k] == album_and_photos[m]:
                final_album.append([album_id[k]], [album_and_photos[m]])
                k += 1
                m -= 1

    return final_album


def save_by_id():
    full_album = albums_with_photos()
    for i in range(len(full_album)):
        for j in range(len(full_album)):
            print(full_album[i][j])


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
