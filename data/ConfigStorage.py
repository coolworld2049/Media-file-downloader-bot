import configparser

"""create file config.ini"""
configParser = configparser.ConfigParser()
path = 'config.ini'
configParser.read(path)


def create_file():
    configParser.read(path)

    configParser['VK_ACC_DATA'] = {'vk_app_id': 8109852,
                                   'vk_token': '',
                                   'token_expires_in': '',
                                   'vk_user_id': ''}

    configParser['BOT_DATA'] = {'BOT_TOKEN': '',
                                'HEROKU_APP_NAME': 'media-downloader-tg',
                                'WEBAPP_PORT': 8000}

    configParser['YA_DISK_DATA'] = {'Y_API_TOKEN': '',
                                    'Y_APP_ID': '131f4986553d493184f6a5e5af832174'}

    configParser.write(open("config.ini", "w"))