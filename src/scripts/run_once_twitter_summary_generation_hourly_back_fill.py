import os
from utils.Utilities import TwitterTopic
from utils.TweetSummarizer import TweetSummarizer
from utils.Logging import info

"""
This script is used to generate hourly tweet summary back fill.
It will generate summary for all the tweets in the past hour. 
usage: python back_fill_twitter_summary_generation.py
"""

tweet_processor_by_topic = {topic.value: TweetSummarizer(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets'), topic.value)
    for topic in TwitterTopic}

for tweet_processor in tweet_processor_by_topic.values():
    tweet_processor.summarize_hourly_tweets_if_necessary(True)
info(f"Back fill tweet summary finished")
