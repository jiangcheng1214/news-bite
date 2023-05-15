# 定义消费者任务，这里将读取Redis Stream中的数据
import json
import redis
from utils.BufferedRedisWriter import BufferedRedisWriter
from utils.Utilities import get_current_hour, get_today_date

# 定义Stream的名称
stream_name = 'twitter_stream'

REDISDB = 1
# 创建一个Celery实例
# app = Celery('twitter_stream', broker='redis://localhost:6379/'+REDISDB)

# 连接到Redis
redis_client = redis.Redis(host='localhost', port=6379, db=REDISDB)

def consumer_task():
    last_id = '0'  # 从流的开始部分开始读取
    raw_buffered_writer = BufferedRedisWriter(master_key,'raw')
    while True:
        # 从 'twitter_stream' 读取数据
        # BLOCK 为 0 表示如果没有更多的消息，就一直等待
        messages = redis_client.xread({stream_name: last_id}, block=0)

        for message in messages:
            stream, message_id, data = message
            # 解析tweet和authorMetadata
            tweet = json.loads(data.get('tweet', '{}'))
            author_metadata = json.loads(data.get('authorMetadata', '{}'))

            print(f'stream: {stream}')
            print(f'Message ID: {message_id}')
            print(f'Tweet: {json.dumps(tweet, indent=4)}')
            print(f'Author Metadata: {json.dumps(author_metadata, indent=4)}')

            # 更新 last_id 以便下次读取新的消息
            last_id = message_id    
            
            master_key = "tweets" + ":" + 'financial' 
            raw_buffered_writer.sub_key_prefix = 'raw'
            raw_buffered_writer.filename_date = get_today_date()
            raw_buffered_writer.filename_hour = get_current_hour()
            raw_buffered_writer.append(json.dumps({'tweet': tweet, 'authorMetadata': author_metadata}))
