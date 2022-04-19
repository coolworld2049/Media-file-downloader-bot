import os

from pytube import YouTube


class DownloadYt:

    @staticmethod
    async def download_file(youtube_video_url):
        yt_obj = YouTube(youtube_video_url)
        yt_obj = yt_obj.streams.get_by_resolution('360p')
        video_title = yt_obj.default_filename
        yt_obj.download(output_path='temp/')
        return video_title

    @staticmethod
    async def delete_temp(video: str):
        os.remove(f'temp/{video}')
