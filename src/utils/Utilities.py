from enum import Enum
import datetime
import re

RAW_TWEET_FILE_PREFIX = 'raw_'
SUM_TWEET_FILE_PREFIX = 'sum_'
INTRA_DAY_SUMMARY_FILE_PREFIX = 'agg_'
INTRA_DAY_SUMMARY_ENRICHED_FILE_PREFIX = 'enriched_'

MINIMAL_OPENAI_API_CALL_INTERVAL_SEC = 0.2
MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING = 30

TWEET_LENGTH_CHAR_LIMIT = 280
TWEET_CONTENT_BUFFER = 6
TWEET_ONE_TIME_POST_LIMIT = 5

DEFAULT_REDIS_CACHE_EXPIRE_SEC = 60 * 60 * 24 * 7  # 7 days


class TwitterTopic(Enum):
    FINANCE = 'finance'
    TECHNOLOGY = 'technology'
    CRYPTO_CURRENCY = 'crypto_currency'


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


def get_clean_tweet_text(raw_text):
    new_line_free_text = raw_text.replace('\n', ' ')
    link_free_text = re.sub(r'http\S+', '', new_line_free_text)
    link_free_clean_text = re.sub(' +', ' ', link_free_text)
    return link_free_clean_text
