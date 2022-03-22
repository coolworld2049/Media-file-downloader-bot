import os
import sys

from aiogram.utils import executor

from telegram_bot.server import dp
from pathlib import Path

# storage downloaded files




def start_telegram_bot():
    executor.start_polling(dp)


def signal_handler():
    print('You pressed Ctrl+C!')
    sys.exit(0)


if __name__ == "__main__":
    try:
        start_telegram_bot()
        test_list = [
            [281821142, 457248715],
            [281821751, 457248714],
            [281175201, 457248684],
            [281175201, 457248683],
            [281175201, 457248677],
            [281175201, 457248676],
            [281175201, 457248675],
            [281175201, 457248674]]

        alb_list = [281821142, 281821751, 281175201]

        """for i in range(len(test_list)):
            print(test_list[i][0])
        for i in range(len(test_list)):
            for j in range(len(test_list[i])+1):
                print(test_list[i][j+1])"""

    except KeyboardInterrupt:
        signal_handler()
