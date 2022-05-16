import os
from pathlib import Path

from pkg_resources import parse_requirements
from setuptools import setup, find_packages


def set_env_vars():
    os.environ.setdefault('BOT_TOKEN', '')
    os.environ.setdefault('DEVELOPER_KEY', '')
    os.environ.setdefault('vk_app_secret', '')
    os.environ.setdefault('vk_app_service', '')
    os.environ.setdefault('ya_client_id', '')
    os.environ.setdefault('ya_client_secret', '')


def setup_py():
    set_env_vars()
    with Path('requirements.txt').open('r', encoding='UTF-16') as requirements_txt:
        install_requires = [
            str(requirement)
            for requirement in parse_requirements(requirements_txt.readlines())
        ]
        print(install_requires)
    setup(
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