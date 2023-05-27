import json
import os
from dotenv import load_dotenv
from twitter.TwitterFilterRulesManager import TwitterFilterRulesManager
from utils.Constants import TWITTER_BEARER_TOKEN_EVAR_KEY, RAW_TWEET_FILE_PREFIX
from utils.TextEmbeddingCache import TextEmbeddingCache
from utils.Decorators import rabbitmq_decorator
from utils.Logging import info, warn
from utils.BufferedFileWriter import BufferedFileWriter
from twitter.TwitterFilteredStreamer import TwitterFilteredStreamer
from twitter.TwitterUserLooker import TwitterUserLooker
from utils.Utilities import TwitterTopic

"""
This script is used to monitor twitter stream and save tweets to file.
usage: python start_twitter_stream_monitor.py
"""

load_dotenv()
bearer_token = os.getenv(TWITTER_BEARER_TOKEN_EVAR_KEY)

assert (len(bearer_token) > 0, "Twitter key is not set")

user_looker = TwitterUserLooker(bearer_token)
total_received = 0
monitored_topic = TwitterTopic.TECHNOLOGY_FINANCE.value
raw_tweets_file_writer = BufferedFileWriter(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', monitored_topic), RAW_TWEET_FILE_PREFIX)

# @rabbitmq_decorator('twitter_raw_data')


def callback(tweet, matching_topic):
    if matching_topic != monitored_topic:
        warn(
            f'Unexpected topic {matching_topic} received. Expected {monitored_topic}')
        return
    global total_received
    author_metadata = user_looker.lookup_user_metadata(tweet['author_id'])
    complete_tweet_received = {'tweet': tweet,
                               'authorMetadata': author_metadata}
    total_received += 1
    author_name = complete_tweet_received['authorMetadata']['name']
    followers_count = complete_tweet_received['authorMetadata']['public_metrics']['followers_count']
    stats_string = f'New tweet received from {author_name} with {followers_count} followers. Total received: {total_received}'
    info(stats_string)
    raw_tweets_file_writer.append(
        json.dumps(complete_tweet_received))
    # cache the tweet text embedding for later use
    TextEmbeddingCache.get_instance().embedding_of(tweet['text'])


twitterFilterRulesManager = TwitterFilterRulesManager(
    bearer_token, [monitored_topic])
streamer = TwitterFilteredStreamer(
    bearer_token, twitterFilterRulesManager, callback)
streamer.start_stream()
