import os
from celery import Celery

from dotenv import load_dotenv
import json

import redis
from twitter.TwitterFilteredStreamer import TwitterFilteredStreamer
from twitter.TwitterUserLooker import TwitterUserLooker
from utils.BufferedFileWriter import BufferedFileWriter
from utils.BufferedRedisWriter import BufferedRedisWriter
from utils.RedisClient import RedisClient
from utils.Utilities import RAW_TWEET_FILE_PREFIX, TwitterTopic, get_current_hour, get_today_date
from utils.Logging import info

load_dotenv()
key = os.getenv("TWITTER_BEARER_TOKEN")
print(key)

user_looker = TwitterUserLooker(key)
total_received = 0
complete_tweets_received_by_topic = {topic.value: [] for topic in TwitterTopic}
raw_tweets_file_writer_by_topic = {topic.value: BufferedRedisWriter('tweets'+":"+topic.value, "raw")
    for topic in TwitterTopic}
tweet_count_by_topic = {topic.value: 0 for topic in TwitterTopic}

# Add more topics here if needed
monitored_topics = [TwitterTopic.FINANCE.value]

# 定义Stream的名称
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
    
    # 将数据作为新的消息添加到Redis Stream
    tweet['tweet_type'] = matching_topic
    RedisClient.connect().xadd('twitter_stream', {'tweet':json.dumps(tweet),'authorMetadata':json.dumps(author_metadata)})

fetcher = TwitterFilteredStreamer(key, monitored_topics, callback)
fetcher.start_stream()









