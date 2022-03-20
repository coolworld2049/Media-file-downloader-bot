import configparser
import time
import webbrowser
import pyautogui
import pyperclip

from urllib.parse import urlparse
from urllib.parse import parse_qs


# variables
vk_app_id = 8090088

# storage file
config = configparser.ConfigParser()
config.read('config.ini')
config['VK_ACC_DATA'] = {'vk_app_id': vk_app_id,
                         'vk_token': '',
                         'vk_user_id': ''}
config.write(open("config.ini", "w+"))


def auth_user(scopes: str = "photos,docs"):
    try:
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={vk_app_id}&display=page&redirect_uri=https://oauth.vk.com/blank.html" \
                     f".com/blank.html&scope={scopes}&response_type=token&v=5.131"
        webbrowser.open_new_tab(oAuth_link)

        pyautogui.click(0, 200)  # a random click for focusing the browser
        pyautogui.press('f6')

        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        vk_response_url = pyperclip.paste()  # for copying the selected url
        print(vk_response_url)

        parsed_url = urlparse(vk_response_url)
        access_token = parse_qs(parsed_url.query)['access_token'][0]
        user_id = parse_qs(parsed_url.query)['user_id'][0]

        print(access_token)
        print(user_id)

        config.set("VK_ACC_DATA", "vk_token", 'as')
        config.write(open("config.ini", "w"))
        return 'Вы авторизованы'
    except BaseException as e:
        return f'Ошибка авторизации{e.args}'
