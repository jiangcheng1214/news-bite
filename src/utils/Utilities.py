from enum import Enum
import datetime

RAW_TWEET_FILE_PREFIX = 'raw_'
CLEAN_TWEET_FILE_PREFIX = 'cln_'
SUM_TWEET_FILE_PREFIX = 'sum_'


class TwitterTopic(Enum):
    FINANCIAL = 'financial'
    TECHNOLOGY = 'technology'
    CRYPTO_CURRENCY = 'crypto_currency'


def get_current_minute():
    now = datetime.datetime.now()
    return now.minute


def get_current_hour():
    now = datetime.datetime.now()
    return now.hour


def get_current_date():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d")


def get_date(time):
    return time.strftime("%Y%m%d")
