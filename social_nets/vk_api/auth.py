import configparser
import time
import webbrowser
import pyautogui
import pyperclip


# variables
vk_app_id = 8109852
scopes: str = "friends,photos,video,notes,wall,docs"

# storage file
config = configparser.ConfigParser()
config.read('config.ini')
config['VK_ACC_DATA'] = {'vk_app_id': vk_app_id,
                         'vk_token': '',
                         'token_expires_in': '',
                         'vk_user_id': ''}
config.write(open("config.ini", "w"))


def auth_user():
    try:
        oAuth_link = f"https://oauth.vk.com/authorize?client_id={vk_app_id}&display=page&redirect_uri=https://oauth.vk.com/blank.html" \
                     f".com/blank.html&scope={scopes}&response_type=token&v=5.131"
        webbrowser.open_new_tab(oAuth_link)

        pyautogui.click(0, 200)  # a random click for focusing the browser
        pyautogui.press('f6')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        vk_response_url: str = pyperclip.paste()  # for copying the selected url

        split_url = vk_response_url.split('#').copy()
        split_var = split_url[1].split('&')

        access_token = split_var[0].split('=')[-1:]
        expires_in = split_var[1].split('=')[-1:]
        user_id = split_var[2].split('=')[-1:]

        config.set("VK_ACC_DATA", "vk_token", access_token[0])
        config.set("VK_ACC_DATA", "token_expires_in", expires_in[0])
        config.set("VK_ACC_DATA", "vk_user_id", user_id[0])
        config.write(open("config.ini", "w"))
        return 'Вы авторизованы'

    except BaseException as e:
        return f'Ошибка авторизации{e.args}'
