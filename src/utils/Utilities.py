from enum import Enum
import datetime
import re
import pyshorteners
from moviepy.editor import *

from utils.Logging import info, warn, error


class TwitterTopic(Enum):
    TECHNOLOGY_FINANCE = 'technology_finance'
    INFLUENCERS = 'influencers'
    POSSIBLE_PORN_INFLUENCERS = 'possible_porn_influencers'


class TwitterTopicMatchScoreSeeds(Enum):
    TECHNOLOGY_FINANCE = ['technology news', 'financial news', 'stock market',
                          'fiscal policy', 'monetory policy', 'federal reserve',
                          'artificial intelligence', 'crypto currency news', 'breaking news',
                          'celebrity scandal', 'celebrity affair', 'technology announcement']


class OpenaiModelVersion(Enum):
    GPT3_5 = 0
    GPT4 = 1


class OpenaiFinishReason(Enum):
    STOP = 'stop'
    LENGTH = 'length'
    CONTENT_FILTER = 'content_filter'
    NULL = 'null'


def get_current_minute():
    now = datetime.datetime.now()
    return now.minute


def get_current_hour():
    now = datetime.datetime.now()
    return now.hour


def get_today_date(format="%Y%m%d"):
    now = datetime.datetime.now()
    return now.strftime(format)


def get_yesterday_date(format="%Y%m%d"):
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    return yesterday.strftime(format)


def get_date(time):
    return time.strftime("%Y%m%d")


def get_previous_day_date(yyyymmdd: str):
    date_format = "%Y%m%d"
    date = datetime.datetime.strptime(yyyymmdd, date_format)
    previous_day = date - datetime.timedelta(days=1)
    return previous_day.strftime(date_format)


def get_clean_text(raw_text):
    new_line_free_text = raw_text.replace('\n', ' ')
    link_free_text = re.sub(r'http\S+', '', new_line_free_text)
    link_free_clean_text = re.sub(' +', ' ', link_free_text)
    return link_free_clean_text.strip()


def clean_summary(summary: str):
    cleaned_text = summary.strip()
    cleaned_text = re.sub(r'^\d+\.?\s*', '', cleaned_text)
    cleaned_text = re.sub(r'^-\s*', '', cleaned_text)
    cleaned_text = re.sub(r'^\"|\"$', '', cleaned_text)
    return cleaned_text


def shorten_url(url):
    url_shortener = pyshorteners.Shortener()
    return url_shortener.tinyurl.short(url)


def trim_video(video_file_path, start_time_sec, end_time_sec):
    if start_time_sec >= end_time_sec:
        warn("trim_video: start_time_sec is less than end_time_sec")
        return video_file_path
    clip = VideoFileClip(video_file_path)
    if clip.duration < end_time_sec:
        warn("trim_video: end_time_sec is greater than video duration")
        return video_file_path
    clip = clip.subclip(start_time_sec, end_time_sec)
    prefix = 'trimmed_'
    file_dir = os.path.dirname(video_file_path)
    file_name = os.path.basename(video_file_path)
    video_file_path = os.path.join(file_dir, prefix + file_name)
    clip.write_videofile(video_file_path, audio_codec='aac')
    return video_file_path
