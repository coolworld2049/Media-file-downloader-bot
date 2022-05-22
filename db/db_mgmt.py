import datetime
import sqlite3

import pandas as pd
import sqlite_utils
from aiogram.types import User
from datetime import datetime as dt

from sqlite_utils import Database

from core import logger


def __create_user_table(users_db: Database):
    users_db["user"].create(
        {
            "user_id": int,
            "language_code": str,
            "username": str,
            "first_name": str,
            "last_name": str,
            "user_url": str,
            "last_seen": float,
            "cloud_storage": str,
            "auth_attempts": int,
            "vk_token": str,
            "vk_user_id": int,
            "vk_token_expires_in": int,
            "vk_user_authorized": bool,
            "vk_photo_download_completed": bool,
            "vk_docs_download_completed": bool,
            "total_number_downloaded_file": int,
            "y_api_token": str,
            "ya_user_authorized": bool,
            "ya_upload_completed": bool,
            "total_number_uploaded_file": int
        }, pk="user_id", if_not_exists=True)


def __add_user_to_db(user: User, users_db: sqlite_utils.Database):
    users_db["user"].insert_all(
        [
            {
                "user_id": user.id,
                "language_code": user.language_code,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_url": user.url,
                "last_seen": dt.timestamp(dt.now()),
                "cloud_storage": '',
                "auth_attempts": 3,
                "vk_token": '',
                "vk_user_id": 0,
                "vk_token_expires_in": 0,
                "vk_user_authorized": False,
                "vk_photo_download_completed": False,
                "vk_docs_download_completed": False,
                "total_number_downloaded_file": 0,
                "y_api_token": '',
                "ya_user_authorized": False,
                "ya_upload_completed": False,
                "total_number_uploaded_file": 0
            }
        ], pk="user_id", ignore=True)

    users_db['user'].upsert(
        {
            "user_id": user.id,
            "language_code": user.language_code,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_url": user.url,
            "last_seen": dt.timestamp(dt.now()),
            "auth_attempts": 3
        }, pk="user_id")

    users_db[f"{user.id}_calls"].create(
        {
            "id": int,
            "settable_state": str,
            "call_from": str,
        }, pk="id", if_not_exists=True)

    users_db[f"{user.id}_photos"].create(
        {
            "id": int,
            "photo_url": str,
            "photo_ext": str,
            "album_title": str,
        }, pk="id", if_not_exists=True)

    users_db[f"{user.id}_docs"].create(
        {
            "id": int,
            "docs_url": str,
            "docs_ext": str,
            "title": str
        }, pk="id", if_not_exists=True)


def __delete_user_tables(user: User, users_db: sqlite_utils.Database):
    users_db.conn.execute(f"DELETE FROM user WHERE user_id = {user.id}")
    users_db[f"{user.id}_calls"].drop()
    users_db[f"{user.id}_photos"].drop()
    users_db[f"{user.id}_docs"].drop()


def export_db(user: User):
    conn = sqlite3.connect('db/users_db.db')
    try:
        # export only user table
        sql_query = pd.read_sql_query(
            f"SELECT * FROM user WHERE user_id = '{user.id}'", conn)
        pd.DataFrame(sql_query).to_csv(
            rf'db/{datetime.date.today()} user_id {user.id}.csv', index=False)
    except sqlite3.Error as error:
        logger.info("Error while connecting to sqlite:", error.args)
    finally:
        if conn:
            conn.close()
            logger.info(f"The SQLite connection (export_csv.py) is closed.\n"
                        f" Created table backup '{datetime.date.today()} user_id {user.id}.csv'")