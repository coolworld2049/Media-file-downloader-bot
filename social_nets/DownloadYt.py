from concurrent.futures import ThreadPoolExecutor

from yt_dlp import YoutubeDL


class DownloadYt:
    def __init__(self):
        self.file_path = "temp/member videos"
        self.ext = '.mp4'

    async def download_video_locally(self, url: str):
        yt_dlp = YoutubeDL({'outtmpl': f'temp/member videos/%(title)s{self.ext}'})
        with ThreadPoolExecutor() as executor:
            executor.map(yt_dlp.download([url]))
            with yt_dlp:
                result = yt_dlp.extract_info(url, download=False)
                return f'temp/member videos/{result["title"]}{self.ext}'
