from aiogram.utils import executor
from memory_profiler import profile

from core import dp, fp
from handlers.start_handler import register_handlers_main
from handlers.vk_handlers import register_handlers_vk
from handlers.yt_handlers import register_handlers_yt


@profile(stream=fp, precision=4)
def main():
    register_handlers_main(dp)
    register_handlers_vk(dp)
    register_handlers_yt(dp)
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
