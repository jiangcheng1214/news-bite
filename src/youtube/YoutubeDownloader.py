from pytube import YouTube


class YoutubeDownloader:
    def __init__(self):
        pass

    def download(self, url: str):
        try:
            yt = YouTube(url)
        except:
            print("YouTube Connection Error")
        print(yt.title)
        try:
            yt.streams.first().download('~/Downloads/test.mp4')
        except Exception as e:
            print("YouTube Download Error" + str(e))


if __name__ == "__main__":
    downloader = YoutubeDownloader()
    downloader.download("https://www.youtube.com/watch?v=5k2RG5taXXE")
