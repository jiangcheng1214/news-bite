import datetime
import os
from utils.Utilities import TwitterTopic
from utils.TweetSummarizer import TweetSummarizer
from utils.Logging import info
import time

"""
This script is used to generate hourly tweet summary
usage: python start_twitter_summary_generation.py
"""

tweet_processor_by_topic = {topic.value: TweetSummarizer(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), topic.value)
    for topic in TwitterTopic}

while True:
    for tweet_processor in tweet_processor_by_topic.values():
        tweet_processor.summarize_hourly_tweets_if_necessary(False)
    now = datetime.datetime.now()
    next_hour = (now + datetime.timedelta(hours=1)
                 ).replace(minute=0, second=0, microsecond=0)
    time_diff = (next_hour - now).seconds
    print(f"Seconds until the next hour starts: {time_diff}")
    time.sleep(time_diff+5)
