import configparser
import json
import time
import random
import requests

config = configparser.ConfigParser()
config.read('config.ini')


def docs_get(count=0):
    api = requests.get("https://api.vk.com/method/docs.get", params={
        'access_token': config['VK_ACC_DATA']['vk_token'],
        'count': count,
        'v': 5.131
    })

    with open("docs data.json", "w") as write_file:
        json.dump(json.loads(api.text), write_file, indent=4)
        write_file.close()

    return json.loads(api.text)


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


terminate = True
