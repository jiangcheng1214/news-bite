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
TWEET_DEFAULT_POST_LIMIT = 5
TWEET_MATCH_SCORE_THRESHOLD_FOR_URL_APPENDING = 0.88
TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD = 0.8
TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD = 0.9

DEFAULT_REDIS_CACHE_EXPIRE_SEC = 60 * 60 * 24 * 7  # 7 days
REDIS_POSTED_TWEETS_KEY = 'posted_tweets'
REDIS_TWEET_EMBEDDING_DICT_KEY = 'tweet_embedding_dict'


class TwitterTopic(Enum):
    FINANCE = 'finance'
    TECHNOLOGY = 'technology'
    CRYPTO_CURRENCY = 'crypto_currency'


class TwitterTopicMatchScoreSeed(Enum):
    FINANCE = 'stock market financial news'
    TECHNOLOGY = 'technology news'
    CRYPTO_CURRENCY = 'crypto currency news'


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


def get_clean_tweet_text(raw_text):
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
