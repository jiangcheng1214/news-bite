
import sys
import os
from utils.Logging import info, error
from utils.TweetSummarizer import TweetSummarizer

from utils.Utilities import TwitterTopic, get_yesterday_date

"""
This script is used to aggregate HOURLY tweet summary and generate DAILY tweet summary.
usage: python daily_summary.py
"""

explicit_date_from_user = sys.argv[1] if len(sys.argv) > 1 else None
if explicit_date_from_user:
    if len(explicit_date_from_user) != 8:
        error(f"explicit_date_from_user must be in format of 'YYYYMMDD'")
        sys.exit(1)
    SUMMRAY_DATE = explicit_date_from_user
else:
    SUMMRAY_DATE = get_yesterday_date()

tweet_summarizers = [TweetSummarizer(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), topic.value) for topic in TwitterTopic]
for summarizer in tweet_summarizers:
    summarizer.summarize_daily_tweets(SUMMRAY_DATE)
info(f"Daily tweet summary finished")
