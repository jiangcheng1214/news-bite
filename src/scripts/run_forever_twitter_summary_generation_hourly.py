import datetime
import os
from utils.Utilities import TwitterTopic, get_yesterday_date
from utils.TweetSummarizer import TweetSummarizer
from twitter.TwitterAPIManager import TwitterAPIManager
from utils.Logging import info
import time

"""
This script is used to generate hourly tweet summary
usage: python start_twitter_summary_generation.py
"""

tweet_summarizers = [TweetSummarizer(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), topic.value) for topic in TwitterTopic]

while True:
    for tweet_summarizer in tweet_summarizers:
        tweet_summarizer.summarize_hourly_tweets_if_necessary(False)
    now = datetime.datetime.now()
    if now.hour == 0:
        date = get_yesterday_date()
        for tweet_summarizer in tweet_summarizers:
            tweet_summarizer.summarize_daily_tweets(date)
            tweet_summarizer.enrich_daily_summary(date)
            TwitterAPIManager().upload_daily_summary(date, TwitterTopic.FINANCIAL.value)
    next_hour = (now + datetime.timedelta(hours=1)
                 ).replace(minute=0, second=0, microsecond=0)
    time_diff = (next_hour - now).seconds
    info(f"Seconds until the next hour starts: {time_diff}")
    time.sleep(time_diff+5)
