from pytube import YouTube, Playlist


class DownloadYt:
    def __init__(self):
        self.callback_url = ''

    def download_file(self):
        yt = YouTube(self.callback_url)
        title = yt.title
        thumbnail = yt.thumbnail_url
        video = yt.streams.filter(progressive=True,
                                  file_extension='mp4',
                                  resolution='1080p').first().download()
        return yt
