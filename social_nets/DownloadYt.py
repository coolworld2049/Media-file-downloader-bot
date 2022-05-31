import asyncio
import logging
from pathlib import Path

from asynccpu import ProcessTaskPoolExecutor
from yt_dlp import YoutubeDL


class DownloadYt:
    def __init__(self):
        self.file_path = "temp/member videos"
        self.ext = '.mp4'

    async def download_video_worker(self, user_id: int, url: str):
        yt_dlp = YoutubeDL({'outtmpl': f'{self.file_path}/{user_id}/%(title)s{self.ext}'})
        info = yt_dlp.extract_info(url, download=False)
        logging.info(f'user_id: {user_id} download_video_worker(user_id, url:{url}).'
                     f' Video: {info["title"]}')
        yt_dlp.download([url])
        return Path(f'{self.file_path}/{user_id}/{info["title"]}{self.ext}')

    async def download_video_controller(self, user_id, url):
        with ProcessTaskPoolExecutor(max_workers=3, cancel_tasks_when_shutdown=True) as executor:
            awaitable = executor.create_process_task(self.download_video_worker, user_id, url)
            return await asyncio.gather(awaitable)
