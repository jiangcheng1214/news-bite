# 定义消费者任务，这里将读取Redis Stream中的数据
import json
from utils.BufferedRedisWriter import BufferedRedisWriter
from utils.Utilities import get_current_hour, get_today_date

def consumer_task():
    raw_buffered_writer = BufferedRedisWriter('tweets:', 'raw')
    # fetch last_id from Redis
    last_id = raw_buffered_writer.redis.get('last_id')
    if last_id is None:
        last_id = '0'  # fallback to '0' if last_id does not exist

    while True:
        messages = raw_buffered_writer.redis.xread({'twitter_stream': last_id.decode('utf-8')})

        for _, message_list in messages:
            for message in message_list:
                message_id, data = message
                tweet = json.loads(data.get(b'tweet', b'{}').decode('utf-8'))
                author_metadata = json.loads(data.get(b'authorMetadata', b'{}').decode('utf-8'))
                tweet_type = data.get(b'tweet_type', b'').decode('utf-8')

                print(f'Message ID: {message_id}')
                print(f'Tweet: {json.dumps(tweet, indent=4)}')
                print(f'Author Metadata: {json.dumps(author_metadata, indent=4)}')

                last_id = message_id
                # store last_id to Redis
                raw_buffered_writer.redis.set('last_id', last_id)

                raw_buffered_writer.master_key += tweet_type
                raw_buffered_writer.sub_key_prefix = 'raw'
                raw_buffered_writer.filename_date = get_today_date()
                raw_buffered_writer.filename_hour = get_current_hour()
                raw_buffered_writer.append(json.dumps({'tweet': tweet, 'authorMetadata': author_metadata, 'tweet_type': tweet_type}))


consumer_task()

