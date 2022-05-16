from yt_dlp import YoutubeDL

from core import bot


class DownloadYt:
    def __init__(self):
        self.file_path = "temp/member videos"
        self.ext = '.mp4'

    async def download_video_locally(self, user_id: int, url: str):
        """bot_name, file_path, chat_id, duration, file_name, width, height"""
        yt_dlp = YoutubeDL({'outtmpl': f'temp/member videos/%(title)s{self.ext}'})
        """yt_dlp.download([url])
        with yt_dlp:
            result = yt_dlp.extract_info(url, download=False)
        if 'entries' in result:
            video_props = result['entries'][0]
        else:
            video_props = result

        bot_info = await bot.get_me()
        message = {
            'bot_name': f"@{bot_info.username}",
            'file_path': str(self.file_path + f'/{video_props["title"]}{self.ext}'),
            'chat_id': user_id,
            'duration': video_props['duration'],
            'file_name': video_props['title'],
            'width': video_props['width'],
            'height': video_props['height']
        }
        return message
        """
        if yt_dlp.download([url]) == 0:
            with yt_dlp:
                result = yt_dlp.extract_info(url, download=False)
            return f'temp/member videos/{result["title"]}{self.ext}'
        else:
            return False
