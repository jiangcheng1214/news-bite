import json
import os
from dotenv import load_dotenv
from utils.Decorators import rabbitmq_decorator
from utils.Logging import info
from utils.BufferedFileWriter import BufferedFileWriter
from twitter.TwitterFilteredStreamer import TwitterFilteredStreamer
from twitter.TwitterUserLooker import TwitterUserLooker
from utils.Utilities import TwitterTopic, RAW_TWEET_FILE_PREFIX, get_clean_text
from twitter.TweetSummaryEnricher import TweetSummaryEnricher

"""
This script is used to monitor twitter stream and save tweets to file.
usage: python start_twitter_stream_monitor.py
"""

load_dotenv()
key = os.getenv("TWITTER_BEARER_TOKEN")

assert (len(key) > 0, "Twitter key is not set")

user_looker = TwitterUserLooker(key)
total_received = 0
complete_tweets_received_by_topic = {topic.value: [] for topic in TwitterTopic}
raw_tweets_file_writer_by_topic = {topic.value: BufferedFileWriter(os.path.join(os.path.dirname(
    __file__),  '..', '..', 'data', 'tweets', topic.value), RAW_TWEET_FILE_PREFIX)
    for topic in TwitterTopic}

# Add more topics here if needed
monitored_topics = [TwitterTopic.FINANCE.value]

tweet_count_by_topic = {topic: 0 for topic in monitored_topics}
enricher = TweetSummaryEnricher()

# @rabbitmq_decorator('twitter_raw_data')
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
    for t in tweet_count_by_topic.keys():
        stats_string += f' {t}:{tweet_count_by_topic[t]}'
    info(stats_string)
    raw_tweets_file_writer_by_topic[matching_topic].append(
        json.dumps(complete_tweet_received))
    # cache the tweet text embedding for later use
    clean_tweet_text = get_clean_text(tweet['text'])
    enricher.get_text_embedding(clean_tweet_text)
    return [matching_topic, complete_tweet_received]


streamer = TwitterFilteredStreamer(key, monitored_topics, callback)
streamer.start_stream()
