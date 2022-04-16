from pytube import YouTube


class DownloadYt:

    @staticmethod
    async def download_file(youtube_video_url):
        yt_obj = YouTube(youtube_video_url)
        yt_obj = yt_obj.streams.get_by_resolution('720p')
        yt_obj.download(output_path='temp/', filename='video.mp4')
