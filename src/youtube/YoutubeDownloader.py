from utils.Utilities import trim_video
from utils.Logging import info, error
import os
from pytube import YouTube


class YoutubeDownloader:

    def download(self, url: str, filename: str, download_folder: str = None, retry: int = 0, small_size=False):
        try:
            youtube = YouTube(url)
            info(youtube.streams)
            if small_size:
                video = youtube.streams.filter(
                    progressive=True, file_extension='mp4').order_by('resolution').asc().first()
            else:
                video = youtube.streams.filter(
                    progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if not download_folder:
                download_folder = os.path.join(os.path.dirname(
                    __file__), '..', '..', 'data', 'videos')
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)
            download_file = os.path.join(download_folder, filename)
            info(f"Downloading {video.title} to {download_file}")
            video.download(output_path=download_folder,
                           filename=filename, skip_existing=False)
            info(f"Downloaded {video.title} to {download_file}")
            return download_file
        except Exception as e:
            error(f"Exception in downloading youtube video: {e}")
            if retry < 3:
                info(f"Retry Download {url}...")
                return self.download(url, filename, download_folder, retry + 1)


if __name__ == "__main__":
    downloader = YoutubeDownloader()
    # download_folder_path = os.path.join(
    #     os.path.dirname(__file__), '..', '..', 'data', 'videos')
    downloader.download(
        "https://www.youtube.com/watch?v=MkBZIfSyeD0", "1min.mp4", small_size=True)
    # youtube = YouTube("https://www.youtube.com/watch?v=5k2RG5taXXE")
    # print(youtube.streams.filter(progressive=True, file_extension='mp4'))
    # video = youtube.streams.filter(
    #                 progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    # print(video.title)
    # trim_video("/Users/chengjiang/Dev/NewsBite/data/videos/test.mp4", 0, 20)
