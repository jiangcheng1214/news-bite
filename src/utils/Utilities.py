from enum import Enum
import datetime
import re


class TwitterTopic(Enum):
    TECHNOLOGY_FINANCE = 'technology_finance'


class TwitterTopicMatchScoreSeed(Enum):
    TECHNOLOGY_FINANCE = 'technology financial news'


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


def get_today_date():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d")


def get_yesterday_date():
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    return yesterday.strftime("%Y%m%d")


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
    return link_free_clean_text


def clean_summary(summary: str):
    cleaned_text = summary.strip()
    cleaned_text = re.sub(r'^\d+\.?\s*', '', cleaned_text)
    cleaned_text = re.sub(r'^-\s*', '', cleaned_text)
    cleaned_text = re.sub(r'^\"|\"$', '', cleaned_text)
    return cleaned_text
    