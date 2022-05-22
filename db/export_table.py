import datetime
import sqlite3

import pandas as pd
from aiogram.types import User

from core import logger


async def export_csv(user: User):
    conn = sqlite3.connect('db/users_db.db')
    try:
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
