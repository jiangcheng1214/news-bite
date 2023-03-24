from enum import Enum
import datetime


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
