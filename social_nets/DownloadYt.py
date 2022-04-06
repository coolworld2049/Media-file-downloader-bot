from pytube import YouTube, Playlist


class DownloadYt:

    @staticmethod
    def download_file(url):
        yt = YouTube(url)
        title = yt.title
        thumbnail = yt.thumbnail_url
        video = yt.streams.filter(progressive=True,
                                  file_extension='mp4',
                                  resolution='1080p')\
            .first().download(filename=title)
