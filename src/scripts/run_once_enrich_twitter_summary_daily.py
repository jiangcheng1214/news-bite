import os
import sys
from utils.Utilities import RAW_TWEET_FILE_PREFIX, get_yesterday_date, DAILY_SUM_ENRICHED_TWEET_FILE_NAME, get_clean_tweet_text, TwitterTopic, DAILY_SUM_TWEET_FILE_NAME, MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING
from utils.TweetSummarizer import TweetSummarizer
from utils.Logging import info, error

"""
This script is used to enrich DAILY tweet summary with more information including original tweet, tweet url, source url, etc.
usage: python enrich_twitter_summary.py
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
    info(
        f"start enriching daily {summarizer.topic} tweet summary for {SUMMRAY_DATE}")
    summarizer.enrich_daily_summary(SUMMRAY_DATE)
