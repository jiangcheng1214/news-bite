import json
import os
from dotenv import load_dotenv
from utils.Constants import TWITTER_BEARER_TOKEN_EVAR_KEY, RAW_TWEET_FILE_PREFIX
from utils.RedisClient import RedisClient
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
key = os.getenv(TWITTER_BEARER_TOKEN_EVAR_KEY)

assert (len(key) > 0, "Twitter key is not set")

user_looker = TwitterUserLooker(key)
total_received = 0
complete_tweets_received = []
monitored_topic = TwitterTopic.TECHNOLOGY_FINANCE.value
raw_tweets_file_writer = BufferedFileWriter(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', monitored_topic), RAW_TWEET_FILE_PREFIX)

def callback(tweet, matching_topic):
    if matching_topic != monitored_topic:
        warn(
            f'Unexpected topic {matching_topic} received. Expected {monitored_topic}')
        return
    global complete_tweets_received, total_received
    author_metadata = user_looker.lookup_user_metadata(tweet['author_id'])
    complete_tweet_received = {'tweet': tweet,
                               'authorMetadata': author_metadata}
    complete_tweets_received.append(
        complete_tweet_received)
    total_received += 1
    author_name = complete_tweet_received['authorMetadata']['name']
    followers_count = complete_tweet_received['authorMetadata']['public_metrics']['followers_count']
    stats_string = f'New tweet received from {author_name} with {followers_count} followers. Total received: {total_received}'
    info(stats_string)
    raw_tweets_file_writer.append(
        json.dumps(complete_tweet_received))
    # cache the tweet text embedding for later use
    TextEmbeddingCache.get_instance().embedding_of(tweet['text'])
    RedisClient.shared().xadd('twitter_stream', {
        'tweet': json.dumps(tweet), 
        'authorMetadata': json.dumps(author_metadata), 
        'tweet_type': matching_topic
    })

streamer = TwitterFilteredStreamer(key, monitored_topic, callback)
streamer.start_stream()