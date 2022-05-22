import os
from pathlib import Path

import setuptools
from pkg_resources import parse_requirements
from setuptools import find_packages

from core import logger


def set_env_vars():
    os.environ['BOT_TOKEN'] = ''
    os.environ['DEVELOPER_KEY'] = ''
    os.environ['vk_app_secret'] = ''
    os.environ['vk_app_service'] = ''
    os.environ['ya_client_id'] = ''
    os.environ['ya_client_secret'] = ''


def setup_py():
    set_env_vars()
    with Path('requirements.txt').open('r', encoding='UTF-16') as requirements_txt:
        install_requires = [
            str(requirement)
            for requirement in parse_requirements(requirements_txt.readlines())
        ]
        logger.debug(install_requires)
    setuptools.setup(
        name='setup.py',
        version='1.0.0',
        packages=find_packages(include=['Social-media-file-downloader', 'Social-media-file-downloader.*']),
        install_requires=install_requires,
        url='https://github.com/coolworld2049/Social-media-file-downloader',
        license='MIT',
        author='coolworld2049',
        author_email='',
        description='Telegram bot to upload files from your VK account, YouTube to cloud storage'
    )


if __name__ == "__main__":
    setup_py()
