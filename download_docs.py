import json
import time
from random import random

import requests


def docs_get(offset=0, count=0):
    from main import vk_token
    api = requests.get("https://api.vk.com/method/docs.get", params={
        'access_token': vk_token,
        'offset': offset,
        'count': count,
        'v': 5.131
    })

    with open("docs data", "w") as write_file:
        json.dump(json.loads(api.text)["response"], write_file, indent=4)

    return json.loads(api.text)


def save_docs():
    data = docs_get()
    count = 1
    items_count = data["response"]["count"]
    i = 0
    while i <= data["response"]["count"]:
        if i != 0:
            data = docs_get(offset=i, count=count)

        for docs in data["response"]["items"]:
            docs_url = docs["url"]
            filename = random.randint(1153, 546864)
            try:
                time.sleep(0.1)
                api = requests.get(docs_url)
                with open(f"Saved docs/{filename}", "wb") as write_file:
                    write_file.write(api.content)
                i += 1
                print(f"{i}/{items_count}")
            except requests.exceptions:
                time.sleep(0.5)
                continue
