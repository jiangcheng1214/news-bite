import datetime
import os
from utils.Utilities import TwitterTopic, get_yesterday_date, get_today_date
from twitter.TweetSummarizer import TweetSummarizer
from twitter.TwitterAPIManager import TwitterAPIManager
from utils.Logging import info, error
import time

"""
This script is used to generate hourly tweet summary
usage: python start_twitter_summary_generation.py
"""

finance_tweet_summarizer = TweetSummarizer(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), TwitterTopic.TECHNOLOGY_FINANCE.value)

# we aggregate news and post to twitter every 3 hours
news_summary_hour_interval = 3


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


if __name__ == "__main__":

    while True:
        try:
            finance_tweet_summarizer.summarize_hourly_tweets_if_necessary(
                False)
            current_start_time = datetime.datetime.now()
            next_hour_start_time = (current_start_time + datetime.timedelta(hours=1)
                                    ).replace(minute=0, second=0, microsecond=0)
            hour = current_start_time.hour
            if hour == 0:
                date = get_yesterday_date()
                hour = 24
            else:
                date = get_today_date()
            if hour % news_summary_hour_interval == 0:
                hourly_summary_file_paths = get_hourly_summary_file_paths(
                    TwitterTopic.TECHNOLOGY_FINANCE.value, date, hour - news_summary_hour_interval, hour)

                summary_file_path = os.path.join(os.path.dirname(
                    __file__),  '..', '..', 'data', 'tweet_summaries', TwitterTopic.TECHNOLOGY_FINANCE.value, date, f"summary_{hour}")
                if not os.path.exists(summary_file_path):
                    finance_tweet_summarizer.summarize_intra_day_tweets(
                        hourly_summary_file_paths, summary_file_path)

                enriched_summary_file_path = os.path.join(os.path.dirname(
                    __file__),  '..', '..', 'data', 'tweet_summaries', TwitterTopic.TECHNOLOGY_FINANCE.value, date, f"summary_{hour}_enriched")
                if not os.path.exists(enriched_summary_file_path):
                    raw_tweet_file_paths = get_raw_tweet_file_paths(
                        TwitterTopic.TECHNOLOGY_FINANCE.value, date, hour - news_summary_hour_interval, hour)
                    finance_tweet_summarizer.enrich_tweet_summary(
                        raw_tweet_file_paths, summary_file_path, enriched_summary_file_path)
                    TwitterAPIManager().upload_summary_items(enriched_summary_file_path)
            sec_until_next_start = (next_hour_start_time -
                                    datetime.datetime.now()).seconds
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start+5)
        except Exception as e:
            error(f"Exception in running twitter summary generation: {e}")
            time.sleep(60)
