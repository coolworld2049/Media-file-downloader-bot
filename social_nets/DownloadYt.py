from pytube import YouTube


class DownloadYt:

    @staticmethod
    def download_file(youtube_video_url):
        yt_obj = YouTube(youtube_video_url)
        yt_obj = yt_obj.streams.first()
        yt_obj.download(output_path='temp/', filename='video.mp4')
        return yt_obj
