import datetime
import os
from utils.Utilities import TwitterTopic, get_yesterday_date, get_today_date
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


def get_hourly_summary_file_paths(topic: str, date, start_hour, end_hour):
    summary_file_folder = os.path.join(os.path.dirname(
        __file__),  '..', '..', 'data', 'tweets', topic, date)
    hourly_summary_file_paths = []
    for hour in range(start_hour, end_hour):
        hourly_summary_file_paths.append(os.path.join(
            summary_file_folder, f"sum_{hour}"))
    return hourly_summary_file_paths

def get_raw_tweet_file_paths(topic: str, date, start_hour, end_hour):
    summary_file_folder = os.path.join(os.path.dirname(
        __file__),  '..', '..', 'data', 'tweets', topic, date)
    hourly_summary_file_paths = []
    for hour in range(start_hour, end_hour):
        hourly_summary_file_paths.append(os.path.join(
            summary_file_folder, f"raw_{hour}"))
    return hourly_summary_file_paths

while True:
    for tweet_summarizer in tweet_summarizers:
        tweet_summarizer.summarize_hourly_tweets_if_necessary(False)
    now = datetime.datetime.now()
    hour = now.hour
    if hour == 6 or hour == 12 or hour == 18:
        today_date = get_today_date()
        hourly_summary_file_paths = get_hourly_summary_file_paths(
            TwitterTopic.FINANCIAL.value, today_date, hour - 6, hour)
        if hour == 6:
            yesterday_date = get_yesterday_date()
            hourly_summary_file_paths.extend(get_hourly_summary_file_paths(
                TwitterTopic.FINANCIAL.value, yesterday_date, 18, 24))

        summary_file_path = os.path.join(os.path.dirname(
            __file__),  '..', '..', 'data', 'tweet_summaries', TwitterTopic.FINANCIAL.value, today_date, f"summary_{hour}.jsons")
        tweet_summarizer.summarize_intra_day_tweets(
            hourly_summary_file_paths, summary_file_path)
        
        raw_tweet_file_paths = get_raw_tweet_file_paths(
            TwitterTopic.FINANCIAL.value, today_date, hour - 6, hour)
        if hour == 6:
            yesterday_date = get_yesterday_date()
            raw_tweet_file_paths.extend(get_raw_tweet_file_paths(
                TwitterTopic.FINANCIAL.value, yesterday_date, 18, 24))
        enriched_summary_file_path = os.path.join(os.path.dirname(
            __file__),  '..', '..', 'data', 'tweet_summaries', TwitterTopic.FINANCIAL.value, today_date, f"summary_{hour}_enriched.jsons")
        tweet_summarizer.enrich_daily_summary(
            raw_tweet_file_paths, summary_file_path, enriched_summary_file_path)
        TwitterAPIManager().upload_daily_summary(enriched_summary_file_path)

    next_hour = (now + datetime.timedelta(hours=1)
                 ).replace(minute=0, second=0, microsecond=0)
    time_diff = (next_hour - now).seconds
    info(f"Seconds until the next hour starts: {time_diff}")
    time.sleep(time_diff+5)
