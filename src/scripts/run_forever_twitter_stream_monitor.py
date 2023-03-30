import json
import os
from dotenv import load_dotenv
from utils.Logging import info
from utils.BufferedFileWriter import BufferedFileWriter
from twitter.TwitterFilteredStreamer import TwitterFilteredStreamer
from twitter.TwitterUserLooker import TwitterUserLooker
from utils.Utilities import TwitterTopic, RAW_TWEET_FILE_PREFIX

"""
This script is used to monitor twitter stream and save tweets to file.
usage: python start_twitter_stream_monitor.py
"""

load_dotenv()
key = os.getenv("TWITTER_KEY")

assert (key is not None, "Twitter key is not set")

user_looker = TwitterUserLooker(key)
total_received = 0
complete_tweets_received_by_topic = {topic.value: [] for topic in TwitterTopic}
raw_tweets_file_writer_by_topic = {topic.value: BufferedFileWriter(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value), RAW_TWEET_FILE_PREFIX)
    for topic in TwitterTopic}
tweet_count_by_topic = {topic.value: 0 for topic in TwitterTopic}


def callback(tweet, matching_topic):
    global complete_tweets_received_by_topic, tweet_count_by_topic, total_received
    author_metadata = user_looker.lookup_user_metadata(tweet['author_id'])
    complete_tweet_received = {'tweet': tweet,
                               'authorMetadata': author_metadata}
    complete_tweets_received_by_topic[matching_topic].append(
        complete_tweet_received)
    tweet_count_by_topic[matching_topic] += 1
    total_received += 1
    author_name = complete_tweet_received['authorMetadata']['name']
    followers_count = complete_tweet_received['authorMetadata']['public_metrics']['followers_count']
    stats_string = f'New tweet received from {author_name} with {followers_count} followers.'
    for t in TwitterTopic:
        stats_string += f' {t.value}:{tweet_count_by_topic[t.value]}'
    info(stats_string)
    raw_tweets_file_writer_by_topic[matching_topic].append(
        json.dumps(complete_tweet_received))


fetcher = TwitterFilteredStreamer(key, callback)
fetcher.start_stream()
