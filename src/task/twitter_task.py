import os

from dotenv import load_dotenv
import json
from news_rest.backend.drf_course.settings import CELERY_RESULT_BACKEND, REDIS_CACHE_ALIAS
from twitter.TwitterFilteredStreamer import TwitterFilteredStreamer
from twitter.TwitterUserLooker import TwitterUserLooker
from utils.Utilities import RAW_TWEET_FILE_PREFIX, TwitterTopic
from utils.Logging import info

load_dotenv()
key = os.getenv("TWITTER_BEARER_TOKEN")

assert (len(key) > 0, "Twitter key is not set")

user_looker = TwitterUserLooker(key)
total_received = 0
complete_tweets_received_by_topic = {topic.value: [] for topic in TwitterTopic}
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
    # raw_tweets_file_writer_by_topic[matching_topic].append(
    #     json.dumps(complete_tweet_received))
    # 将数据作为新的消息添加到Redis Stream
    redis_client.xadd(stream_name + '_' + matching_topic, tweet)

REDISDB = 1
# 创建一个Celery实例
app = CELERY_RESULT_BACKEND('twitter_stream', broker='redis://localhost:6379/'+REDISDB)

# 连接到Redis
redis_client = REDIS_CACHE_ALIAS.Redis(host='localhost', port=6379, db=REDISDB)

# 定义Stream的名称
stream_name = 'twitter_stream'

fetcher = TwitterFilteredStreamer(key, callback)

# 定义生产者任务，这里将从Twitter Stream API获取数据并添加到Redis Stream
@app.task
def producer_task():
    fetcher.start_stream()

# 定义消费者任务，这里将读取Redis Stream中的数据
@app.task
def consumer_task():
    last_id = '0'  # 从流的开始部分开始读取

    while True:
        # 从 'twitter_stream' 读取数据
        # BLOCK 为 0 表示如果没有更多的消息，就一直等待
        messages = redis_client.xread({stream_name: last_id}, block=0)

        for message in messages:
            stream, message_id, tweet = message
            print(f'stream: {stream}')
            print(f'Message ID: {message_id}')
            print(f'Tweet: {json.dumps(tweet, indent=4)}')

            # 更新 last_id 以便下次读取新的消息
            last_id = message_id



