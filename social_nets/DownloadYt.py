import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from yt_dlp import YoutubeDL


class DownloadYt:
    def __init__(self, user_id: int, url: str):
        self.user_id = user_id
        self.source_url = url
        self.file_path = "temp/member videos"
        self.user_dir = f'{self.file_path}/{self.user_id}'
        self._ydl_opts = {'outtmpl': f'{self.file_path}/{self.user_id}/%(id)s.%(ext)s'}
        self.info = YoutubeDL(self._ydl_opts).extract_info(self.source_url, download=False)

    def download_video_worker(self):
        with YoutubeDL(self._ydl_opts) as ydl:
            ydl.download([self.source_url])
            return Path(f'{self.user_dir}/{self.info["id"]}.mp4') if self.info["id"] else None

    def download_audio_worker(self):
        ydl_opts = \
            {
                'outtmpl': self._ydl_opts['outtmpl'],
                'format': 'm4a/bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}]
            }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.source_url])
            return Path(f'{self.user_dir}/{self.info["id"]}.m4a') if self.info["id"] else None

    async def common_controller(self, func):
        try:
            loop = asyncio.get_running_loop()
            with ProcessPoolExecutor() as pool:
                awt = await loop.run_in_executor(pool, func)
                logging.info(f'user_id: {self.user_id} function_coroutine: '
                             f'{func.__name__},'
                             f' args: {self.user_id}, {self.source_url}. Task done')
                return awt
        except Exception as e:
            logging.warning(f'user_id: {self.user_id} function_coroutine: {func.__name__}.'
                            f' Exception: {e.args}')
            return f'user_id: {self.user_id} function_coroutine: {func.__name__}.' \
                   f' Exception: {e.args}'

    async def download_video(self):
        return await self.common_controller(self.download_video_worker)

    async def download_audio(self):
        return await self.common_controller(self.download_audio_worker)
