
import sys
import os
from utils.Logging import info, error
from utils.TweetSummarizer import TweetSummarizer

from utils.Utilities import TwitterTopic

"""
This script is used to aggregate HOURLY tweet summary and generate DAILY tweet summary.
usage: python daily_summary.py
"""

explicit_date_from_user = sys.argv[1] if len(sys.argv) > 1 else None
assert explicit_date_from_user and len(
    explicit_date_from_user) == 8, "date must be passed in with format of 'YYYYMMDD'"


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


finance_tweet_summarizer = TweetSummarizer(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), TwitterTopic.TECHNOLOGY_FINANCE.value)

for hour in [3, 6, 9, 12, 15, 18, 21, 24]:
    summary_file_paths = get_hourly_summary_file_paths(
        finance_tweet_summarizer.topic, explicit_date_from_user, hour - 3, hour)
    summary_file_path = os.path.join(os.path.dirname(
        __file__),  '..', '..', 'data', 'tweet_summaries', finance_tweet_summarizer.topic, explicit_date_from_user, f"summary_{hour}")
    finance_tweet_summarizer.summarize_intra_day_tweets(
        summary_file_paths, summary_file_path)

    raw_tweet_file_paths = get_raw_tweet_file_paths(
        finance_tweet_summarizer.topic, explicit_date_from_user, hour - 3, hour)
    enriched_summary_file_path = os.path.join(os.path.dirname(
        __file__),  '..', '..', 'data', 'tweet_summaries', finance_tweet_summarizer.topic, explicit_date_from_user, f"summary_{hour}_enriched")
    finance_tweet_summarizer.enrich_tweet_summary(
        raw_tweet_file_paths, summary_file_path, enriched_summary_file_path)

info(f"Daily tweet summary finished")
