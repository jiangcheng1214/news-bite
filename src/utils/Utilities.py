from enum import Enum
import datetime
import re

RAW_TWEET_FILE_PREFIX = 'raw_'
CLEAN_TWEET_FILE_PREFIX = 'clean_'
SUM_TWEET_FILE_PREFIX = 'sum_'
DAILY_SUM_TWEET_FILE_NAME = 'daily_sum.jsons'
DAILY_SUM_ENRICHED_TWEET_FILE_NAME = 'daily_sum_enriched.jsons'

MINIMAL_OPENAI_API_CALL_INTERVAL_SEC = 0.2
MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING = 30

class TwitterTopic(Enum):
    FINANCIAL = 'financial'
    TECHNOLOGY = 'technology'
    CRYPTO_CURRENCY = 'crypto_currency'


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


def get_current_date():
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
